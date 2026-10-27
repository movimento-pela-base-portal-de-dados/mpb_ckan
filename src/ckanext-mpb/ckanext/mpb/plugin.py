import json
from collections import OrderedDict

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.mpb import cli
from ckanext.mpb import constants as c


def apply_portal_defaults(config_):
    for key, value in c.PORTAL_DEFAULTS.items():
        if config_.get(key) in (None, c.CKAN_DEFAULTS[key]):
            config_[key] = value


def pesquisa_facets():
    return OrderedDict(c.PESQUISA_FACETS)


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


class MpbPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigDeclaration)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IFacets, inherit=True)
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

    def organization_facets(self, facets_dict, organization_type, package_type):
        return pesquisa_facets()

    # IPackageController

    def before_dataset_index(self, pkg_dict):
        return index_multivalued_fields(pkg_dict)

    def after_dataset_search(self, search_results, search_params):
        return label_facet_items(search_results)
