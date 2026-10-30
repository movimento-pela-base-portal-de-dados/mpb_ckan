import json
from collections import OrderedDict

from flask import has_request_context

import ckan.model as model
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.mpb import cli
from ckanext.mpb import constants as c


def apply_portal_defaults(config_):
    for key, value in c.PORTAL_DEFAULTS.items():
        if config_.get(key) in (None, c.CKAN_DEFAULTS[key]):
            config_[key] = value


def pesquisa_facets():
    facets = OrderedDict(c.PESQUISA_FACETS)
    if not toolkit.get_action("group_list")({"ignore_auth": True}, {"limit": 1}):
        del facets["groups"]
    return facets


def index_multivalued_fields(pkg_dict):
    for index_field, field_name in c.MULTIVALUED_FACETS.items():
        value = pkg_dict.get(field_name)
        if not value:
            continue
        if isinstance(value, str):
            value = json.loads(value) if value.startswith("[") else [value]
        pkg_dict[index_field] = value
    return pkg_dict


def choice_labels():
    schema = toolkit.get_action("scheming_dataset_schema_show")(
        {"ignore_auth": True}, {"type": c.DATASET_TYPE}
    )
    fields = {field["field_name"]: field for field in schema["dataset_fields"]}
    return {
        facet: {choice["value"]: choice["label"] for choice in fields[field_name]["choices"]}
        for facet, field_name in c.CHOICE_FACETS.items()
    }


def label_facet_items(search_results):
    search_facets = search_results.get("search_facets") or {}
    if not search_facets.keys() & c.CHOICE_FACETS.keys():
        return search_results
    for facet, labels in choice_labels().items():
        for item in search_facets.get(facet, {}).get("items", []):
            item["display_name"] = labels.get(item["name"], item["display_name"])
    return search_results


def license_id(key, data, errors, context):
    if data.get(key) in (toolkit.missing, None, ""):
        package = context.get("package")
        data[key] = (package and package.license_id) or c.DEFAULT_LICENSE_ID
    if model.Package.get_license_register().get(data[key]) is None:
        raise toolkit.Invalid("Licença inválida.")


def requested_package_type(data_dict):
    if data_dict and data_dict.get("type"):
        return data_dict["type"]
    if has_request_context():
        return (toolkit.request.view_args or {}).get("package_type")
    return None


@toolkit.chained_auth_function
@toolkit.auth_sysadmins_check
def package_create(next_auth, context, data_dict=None):
    package_type = requested_package_type(data_dict)
    default_type = toolkit.config.get("ckan.default.package_type")
    if package_type and package_type != default_type:
        return {
            "success": False,
            "msg": f"Este portal só aceita datasets do tipo {default_type}.",
        }
    return next_auth(context, data_dict)


class MpbPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigDeclaration)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "mpb")
        apply_portal_defaults(config_)

    # IConfigDeclaration

    def declare_config_options(self, declaration, key):
        declaration.annotate("ckanext-mpb")
        declaration.declare(c.ORGANIZATION_NAME, c.DEFAULT_ORGANIZATION_NAME)
        declaration.declare(c.ORGANIZATION_TITLE, c.DEFAULT_ORGANIZATION_TITLE)
        declaration.declare(c.PIPELINE_USER_NAME, c.DEFAULT_PIPELINE_USER_NAME)
        declaration.declare(c.PIPELINE_USER_EMAIL)

    # IClick

    def get_commands(self):
        return cli.get_commands()

    # IFacets

    def dataset_facets(self, facets_dict, package_type):
        if package_type != c.DATASET_TYPE:
            return facets_dict
        return pesquisa_facets()

    def group_facets(self, facets_dict, group_type, package_type):
        return pesquisa_facets()

    def organization_facets(self, facets_dict, organization_type, package_type):
        return pesquisa_facets()

    # IAuthFunctions

    def get_auth_functions(self):
        return {"package_create": package_create}

    # IValidators

    def get_validators(self):
        return {"mpb_license_id": license_id}

    # IPackageController

    def before_dataset_index(self, pkg_dict):
        return index_multivalued_fields(pkg_dict)

    def after_dataset_search(self, search_results, search_params):
        return label_facet_items(search_results)
