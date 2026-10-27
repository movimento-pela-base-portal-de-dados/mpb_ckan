import pytest

from ckan.tests import factories
from ckan.tests.helpers import call_action

from ckanext.mpb import constants
from ckanext.mpb.plugin import index_multivalued_fields
from ckanext.mpb.tests.test_schema import SCHEMA_OPTION, _pesquisa


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "mpb scheming_datasets"),
    pytest.mark.ckan_config("scheming.dataset_schemas", SCHEMA_OPTION),
    pytest.mark.ckan_config("ckan.default.package_type", "pesquisa"),
]


@pytest.mark.parametrize(
    "etapa,expected",
    [
        ('["ensino_fundamental", "ensino_medio"]', ["ensino_fundamental", "ensino_medio"]),
        (["ensino_medio"], ["ensino_medio"]),
        ("ensino_medio", ["ensino_medio"]),
    ],
)
def test_etapa_is_indexed_as_list(etapa, expected):
    assert index_multivalued_fields({"etapa": etapa})["vocab_etapa"] == expected


@pytest.mark.parametrize("etapa", [None, "", []])
def test_empty_etapa_is_not_indexed(etapa):
    assert "vocab_etapa" not in index_multivalued_fields({"etapa": etapa})


def _create_pesquisas():
    sysadmin = factories.Sysadmin()
    organization = factories.Organization()
    context = {"user": sysadmin["name"]}
    call_action("package_create", context=dict(context), **_pesquisa(organization["id"]))
    call_action(
        "package_create",
        context=dict(context),
        **_pesquisa(
            organization["id"],
            name="mpb-pesquisa-infantil",
            etapa=["educacao_infantil", "ensino_medio"],
            tipo_estudo="guia",
            ano="2023",
        ),
    )


def _facet_items(result, facet):
    return {
        item["name"]: (item["count"], item["display_name"])
        for item in result["search_facets"][facet]["items"]
    }


@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_search_facets_count_and_label_pesquisa_fields():
    _create_pesquisas()

    result = call_action(
        "package_search", **{"facet.field": list(constants.PESQUISA_FACETS)}
    )

    assert _facet_items(result, "vocab_etapa") == {
        "ensino_medio": (2, "Ensino Médio"),
        "ensino_fundamental": (1, "Ensino Fundamental"),
        "educacao_infantil": (1, "Educação Infantil"),
    }
    assert _facet_items(result, "tema") == {"implementacao": (2, "Implementação")}
    assert _facet_items(result, "tipo_estudo") == {
        "estudo_de_caso": (1, "Estudo de caso"),
        "guia": (1, "Guia"),
    }
    assert _facet_items(result, "ano") == {"2024": (1, "2024"), "2023": (1, "2023")}


@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_search_filters_by_etapa():
    _create_pesquisas()

    result = call_action("package_search", fq='vocab_etapa:"educacao_infantil"')

    assert [dataset["name"] for dataset in result["results"]] == ["mpb-pesquisa-infantil"]


@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_search_page_shows_pesquisa_facets(app):
    _create_pesquisas()

    body = app.get("/pesquisa/").get_data(as_text=True)

    for facet, title in constants.PESQUISA_FACETS.items():
        assert (title in body) == (facet != "groups")
    assert "Ensino Médio" in body
    assert "Estudo de caso" in body
    assert "license_id" not in body
    assert "res_format" not in body


@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_categories_facet_appears_when_groups_exist(app):
    group = factories.Group(name="curriculo", title="Currículo")
    _create_pesquisas()
    sysadmin = factories.Sysadmin()
    call_action(
        "member_create",
        context={"user": sysadmin["name"]},
        id=group["id"],
        object="mpb-pesquisa-teste",
        object_type="package",
        capacity="public",
    )

    search_body = app.get("/pesquisa/").get_data(as_text=True)
    group_body = app.get("/group/curriculo").get_data(as_text=True)

    assert "Categorias" in search_body
    assert "Currículo" in search_body
    assert "Etapa" in group_body
    assert "license_id" not in group_body
