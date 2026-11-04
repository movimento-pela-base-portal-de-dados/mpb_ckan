from pathlib import Path

LICENSES_PATH = Path(__file__).parent / "licenses.json"
DEFAULT_LICENSE_ID = "cc-by-4.0"

PORTAL_DEFAULTS = {
    "ckan.site_title": "Portal de Dados Movimento pela Base",
    "ckan.site_logo": "",
    "ckan.site_description": "Dados abertos publicados pelo Movimento pela Base.",
    "ckan.site_about": (
        "O Portal de Dados Movimento pela Base reúne conjuntos de dados "
        "publicados pelo Movimento pela Base e por organizações parceiras."
    ),
    "licenses_group_url": LICENSES_PATH.as_uri(),
}

CKAN_DEFAULTS = {
    "ckan.site_title": "CKAN",
    "ckan.site_logo": "/base/images/ckan-logo.png",
    "ckan.site_description": "",
    "ckan.site_about": "",
    "licenses_group_url": "",
}

ORGANIZATION_NAME = "ckanext.mpb.organization.name"
ORGANIZATION_TITLE = "ckanext.mpb.organization.title"
PIPELINE_USER_NAME = "ckanext.mpb.pipeline_user.name"
PIPELINE_USER_EMAIL = "ckanext.mpb.pipeline_user.email"

DEFAULT_ORGANIZATION_NAME = "movimento-pela-base"
DEFAULT_ORGANIZATION_TITLE = "Movimento pela Base"
DEFAULT_PIPELINE_USER_NAME = "mpb-pipelines"

PIPELINE_USER_CAPACITY = "editor"

DATASET_TYPE = "pesquisa"

PESQUISA_FACETS = {
    "organization": "Organizações",
    "groups": "Categorias",
    "tema": "Grupo temático",
    "vocab_etapa": "Etapa de ensino",
    "tags": "Palavras-chave",
    "tipo_estudo": "Tipo de estudo",
    "ano": "Ano",
}
MULTIVALUED_FACETS = {"vocab_etapa": "etapa"}
CHOICE_FACETS = {"tema": "tema", "vocab_etapa": "etapa", "tipo_estudo": "tipo_estudo"}

CATALOG_PATH = Path(__file__).parent / "catalog.yaml"
SCHEMA_PATH = Path(__file__).parent / "schemas" / "pesquisa.yaml"

SOLR_DATASET_DICTS = {"data_dict", "validated_data_dict"}
ACTIVITY_ACTIONS = (
    "activity_show",
    "package_activity_list",
    "recently_changed_packages_activity_list",
    "dashboard_activity_list",
    "user_activity_list",
    "group_activity_list",
    "organization_activity_list",
)
