import json
import re
from functools import cache

import ckan.authz as authz
import ckan.model as model
import ckan.plugins.toolkit as toolkit
import yaml
from flask import has_request_context

from ckanext.mpb import constants as c

SOLR_FIELD_NAME = re.compile(r"^[A-Za-z0-9_]+$")


@cache
def _schema():
    with c.SCHEMA_PATH.open(encoding="utf-8") as schema_file:
        return yaml.safe_load(schema_file)


@cache
def private_fields():
    return frozenset(
        field["field_name"] for field in _schema()["dataset_fields"] if field.get("mpb_private")
    )


@cache
def search_only_fields():
    return frozenset(
        field["field_name"] for field in _schema()["dataset_fields"] if field.get("mpb_search_only")
    )


@cache
def public_resource_types():
    field = next(
        field for field in _schema()["resource_fields"] if field["field_name"] == "tipo_documento"
    )
    return frozenset(
        choice["value"] for choice in field["choices"] if not choice.get("mpb_private")
    )


def is_public_resource(resource):
    return resource.get("tipo_documento") in public_resource_types()


def can_read_private(user, owner_org):
    if not user:
        return False
    if authz.is_sysadmin(user):
        return True
    return bool(owner_org) and authz.has_user_permission_for_group_or_org(owner_org, user, "read")


def request_user():
    if not has_request_context():
        return None
    user = toolkit.current_user
    return user.name if user and user.is_authenticated else None


def hide_private(pkg_dict):
    hidden = private_fields()
    for field in hidden:
        pkg_dict.pop(field, None)
    if "extras" in pkg_dict:
        pkg_dict["extras"] = [extra for extra in pkg_dict["extras"] if extra["key"] not in hidden]
    pkg_dict["resources"] = [
        resource for resource in pkg_dict.get("resources", []) if is_public_resource(resource)
    ]
    pkg_dict["num_resources"] = len(pkg_dict["resources"])
    return pkg_dict


def filter_dataset(pkg_dict, user):
    if pkg_dict.get("type") == c.DATASET_TYPE and not can_read_private(
        user, pkg_dict.get("owner_org")
    ):
        hide_private(pkg_dict)
    return pkg_dict


def filter_shown_dataset(context, pkg_dict):
    if not context.get("ignore_auth"):
        filter_dataset(pkg_dict, context.get("user"))
    return pkg_dict


def filter_search_results(search_results):
    user = request_user()
    for pkg_dict in search_results.get("results", []):
        filter_dataset(pkg_dict, user)
    return search_results


def restrict_search_params(search_params):
    if authz.is_sysadmin(request_user()):
        return search_params
    fl = search_params.get("fl")
    if fl:
        tokens = re.split(r"[\s,]+", " ".join(fl) if isinstance(fl, list) else fl)
        search_params["fl"] = [
            token
            for token in tokens
            if SOLR_FIELD_NAME.match(token) and token not in c.SOLR_DATASET_DICTS
        ]
    facet_fields = search_params.get("facet.field")
    if facet_fields:
        if isinstance(facet_fields, str):
            facet_fields = json.loads(facet_fields)
        search_params["facet.field"] = [field for field in facet_fields if field != "text"]
    return search_params


def index_public_fields(pkg_dict):
    if pkg_dict.get("dataset_type") != c.DATASET_TYPE:
        return pkg_dict
    validated = json.loads(pkg_dict["validated_data_dict"])
    search_terms = [term for field in search_only_fields() for term in validated.get(field) or []]
    for field in private_fields():
        pkg_dict.pop(field, None)
        pkg_dict.pop(f"extras_{field}", None)
    resources = validated.get("resources", [])
    public = [index for index, resource in enumerate(resources) if is_public_resource(resource)]
    for key, value in list(pkg_dict.items()):
        if key.startswith("res_") and isinstance(value, list) and len(value) == len(resources):
            pkg_dict[key] = [value[index] for index in public]
    pkg_dict["num_resources"] = len(public)
    if search_terms:
        pkg_dict["text"] = list(pkg_dict.get("text") or []) + search_terms
    return pkg_dict


def resource_visible(user, resource_dict):
    package = model.Package.get(resource_dict.get("package_id"))
    if not package or package.type != c.DATASET_TYPE or is_public_resource(resource_dict):
        return True
    return can_read_private(user, package.owner_org)


@toolkit.chained_auth_function
def resource_show(next_auth, context, data_dict=None):
    result = next_auth(context, data_dict)
    if not result.get("success"):
        return result
    resource = model.Resource.get((data_dict or {}).get("id"))
    if resource and not resource_visible(
        context.get("user"), dict(resource.extras or {}, package_id=resource.package_id)
    ):
        return {"success": False, "msg": "Arquivo restrito à equipe da organização."}
    return result


@toolkit.chained_action
@toolkit.side_effect_free
def resource_search(original_action, context, data_dict):
    result = original_action(context, data_dict)
    visible = [
        resource
        for resource in result["results"]
        if resource_visible(context.get("user"), resource)
    ]
    result["count"] -= len(result["results"]) - len(visible)
    result["results"] = visible
    return result


def filter_activities(activities, user):
    for activity in [activities] if isinstance(activities, dict) else activities:
        package = (activity.get("data") or {}).get("package")
        if isinstance(package, dict):
            filter_dataset(package, user)
    return activities


@toolkit.chained_action
@toolkit.side_effect_free
def filter_activity_action(original_action, context, data_dict):
    return filter_activities(original_action(context, data_dict), context.get("user"))


@toolkit.chained_action
@toolkit.side_effect_free
def dataset_followee_list(original_action, context, data_dict):
    return [
        filter_dataset(pkg_dict, context.get("user"))
        for pkg_dict in original_action(context, data_dict)
    ]
