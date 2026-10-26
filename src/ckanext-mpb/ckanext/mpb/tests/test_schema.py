from pathlib import Path

import pytest
import yaml

from ckan.logic import ValidationError
from ckan.tests import factories
from ckan.tests.helpers import call_action


REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
SCHEMA_OPTION = "ckanext.mpb:schemas/pesquisa.yaml"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "pesquisa.yaml"
SCHEMING_SETUP = REPOSITORY_ROOT / "ckan" / "docker-entrypoint.d" / "03_setup_scheming.sh"

# Espelho de src/mpb_data_pipelines/schemas/pesquisa.yaml no mpb-data-pipelines.
PIPELINE_DATASET_FIELDS = {
    "title",
    "name",
    "notes",
    "tag_string",
    "owner_org",
    "tema",
    "etapa",
    "tipo_estudo",
    "ano",
    "observatorio",
    "publico",
    "topico",
    "objetivo",
    "apoio",
    "realizacao",
    "recorte",
    "titulo_alternativo",
    "termos_busca",
}
PIPELINE_RESOURCE_FIELDS = {"url", "name", "format", "tipo_documento"}
PIPELINE_DATASET_CHOICES = {
    "tema": ["conteudo_curricular", "implementacao", "revisao_politica_curricular"],
    "etapa": ["educacao_infantil", "ensino_fundamental", "ensino_medio"],
    "tipo_estudo": [
        "analise",
        "artigo",
        "benchmarking",
        "boa_pratica",
        "curso",
        "estudo_de_caso",
        "guia",
        "pesquisa",
        "recomendacoes",
        "traducao",
    ],
    "observatorio": ["sim", "nao", "site_mpb"],
    "recorte": ["brasil", "estadual", "municipal"],
}
PIPELINE_TIPO_DOCUMENTO_CHOICES = ["relatorio", "sumario_executivo", "ficha_site"]


def _schema():
    with SCHEMA_PATH.open(encoding="utf-8") as schema_file:
        return yaml.safe_load(schema_file)


def test_dataset_schema_has_expected_identity():
    schema = _schema()

    assert schema["scheming_version"] == 2
    assert schema["dataset_type"] == "pesquisa"
    assert schema["dataset_fields"]
    assert schema["resource_fields"]


def _choices(field):
    return [choice["value"] for choice in field["choices"]]


def test_dataset_schema_contains_catalog_metadata_contract():
    schema = _schema()
    dataset_fields = {field["field_name"]: field for field in schema["dataset_fields"]}
    resource_fields = {field["field_name"]: field for field in schema["resource_fields"]}

    assert dataset_fields["title"]["preset"] == "title"
    assert dataset_fields["title"]["required"] is True
    assert dataset_fields["name"]["preset"] == "dataset_slug"
    assert dataset_fields["tag_string"]["required"] is True
    assert dataset_fields["owner_org"]["preset"] == "dataset_organization"
    assert resource_fields["url"]["preset"] == "resource_url_upload"
    assert "format" in resource_fields


def test_dataset_schema_matches_pipeline_mapping_fields():
    schema = _schema()

    assert {field["field_name"] for field in schema["dataset_fields"]} == PIPELINE_DATASET_FIELDS
    assert {field["field_name"] for field in schema["resource_fields"]} == PIPELINE_RESOURCE_FIELDS


def test_dataset_schema_choices_match_pipeline_mapping():
    schema = _schema()
    dataset_fields = {field["field_name"]: field for field in schema["dataset_fields"]}
    resource_fields = {field["field_name"]: field for field in schema["resource_fields"]}

    for field_name, choices in PIPELINE_DATASET_CHOICES.items():
        assert _choices(dataset_fields[field_name]) == choices
    assert _choices(resource_fields["tipo_documento"]) == PIPELINE_TIPO_DOCUMENTO_CHOICES


def test_container_setup_uses_extension_schema():
    setup = SCHEMING_SETUP.read_text()

    assert f'"scheming.dataset_schemas = {SCHEMA_OPTION}"' in setup
    assert '"ckan.default.package_type = pesquisa"' in setup


@pytest.mark.ckan_config("ckan.plugins", "mpb scheming_datasets")
@pytest.mark.ckan_config("scheming.dataset_schemas", SCHEMA_OPTION)
@pytest.mark.ckan_config("ckan.default.package_type", "pesquisa")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_portal_navigation_points_to_pesquisa(app):
    sysadmin = factories.Sysadmin()
    organization = factories.Organization()
    call_action(
        "package_create", context={"user": sysadmin["name"]}, **_pesquisa(organization["id"])
    )

    body = app.get("/").get_data(as_text=True)

    assert 'action="/pesquisa/"' in body
    assert 'href="/pesquisa/?tags=' in body
    assert app.get("/pesquisa/").status_code == 200


@pytest.mark.ckan_config("ckan.plugins", "mpb scheming_datasets")
@pytest.mark.ckan_config("scheming.dataset_schemas", SCHEMA_OPTION)
@pytest.mark.usefixtures("with_plugins")
def test_scheming_loads_extension_schema():
    schema = call_action("scheming_dataset_schema_show", type="pesquisa")

    assert [field["field_name"] for field in schema["dataset_fields"]] == [
        field["field_name"] for field in _schema()["dataset_fields"]
    ]


def _pesquisa(owner_org, **overrides):
    payload = {
        "type": "pesquisa",
        "name": "mpb-pesquisa-teste",
        "title": "Pesquisa de teste",
        "notes": "Resumo sintético usado pela suíte de testes.",
        "tag_string": "currículo,ensino médio",
        "owner_org": owner_org,
        "tema": "implementacao",
        "etapa": ["ensino_fundamental", "ensino_medio"],
        "tipo_estudo": "estudo_de_caso",
        "ano": "2024",
        "observatorio": "sim",
        "publico": ["Gestores", "Professores"],
        "topico": ["Formação"],
        "objetivo": "Objetivo sintético.",
        "apoio": ["Movimento pela Base"],
        "realizacao": ["Instituto de Teste"],
        "recorte": ["estadual"],
        "titulo_alternativo": "Test survey",
        "termos_busca": ["implementação curricular"],
        "resources": [
            {
                "url": "https://example.org/relatorio.pdf",
                "name": "Relatório",
                "format": "PDF",
                "tipo_documento": "relatorio",
            }
        ],
    }
    payload.update(overrides)
    return payload


@pytest.mark.ckan_config("ckan.plugins", "mpb scheming_datasets")
@pytest.mark.ckan_config("scheming.dataset_schemas", SCHEMA_OPTION)
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_pesquisa_is_created_with_schema_fields():
    sysadmin = factories.Sysadmin()
    organization = factories.Organization()

    created = call_action(
        "package_create", context={"user": sysadmin["name"]}, **_pesquisa(organization["id"])
    )
    shown = call_action("package_show", id=created["id"])

    assert shown["etapa"] == ["ensino_fundamental", "ensino_medio"]
    assert shown["publico"] == ["Gestores", "Professores"]
    assert shown["recorte"] == ["estadual"]
    assert str(shown["ano"]) == "2024"
    assert shown["resources"][0]["tipo_documento"] == "relatorio"


@pytest.mark.ckan_config("ckan.plugins", "mpb scheming_datasets")
@pytest.mark.ckan_config("scheming.dataset_schemas", SCHEMA_OPTION)
@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.parametrize(
    "overrides,field_name",
    [
        ({"tema": "inexistente"}, "tema"),
        ({"etapa": ["ensino_superior"]}, "etapa"),
        ({"ano": "dois mil"}, "ano"),
    ],
)
def test_pesquisa_rejects_invalid_values(overrides, field_name):
    sysadmin = factories.Sysadmin()
    organization = factories.Organization()

    with pytest.raises(ValidationError) as error:
        call_action(
            "package_create",
            context={"user": sysadmin["name"]},
            **_pesquisa(organization["id"], **overrides),
        )

    assert field_name in error.value.error_dict
