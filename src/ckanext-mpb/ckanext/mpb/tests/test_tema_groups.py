import pytest
from ckan.tests import factories
from ckan.tests.helpers import call_action

from ckanext.mpb.tests.test_schema import SCHEMA_OPTION, _pesquisa

pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "mpb scheming_datasets"),
    pytest.mark.ckan_config("scheming.dataset_schemas", SCHEMA_OPTION),
    pytest.mark.ckan_config("ckan.default.package_type", "pesquisa"),
    pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index"),
]


@pytest.fixture
def editor_context():
    editor = factories.User()
    organization = factories.Organization(users=[{"name": editor["name"], "capacity": "editor"}])
    return {"user": editor["name"]}, organization["id"]


def _groups(dataset):
    return [(group["name"], group["title"]) for group in dataset["groups"]]


def test_tema_creates_group_and_links_dataset(editor_context):
    context, owner_org = editor_context

    dataset = call_action("package_create", context=dict(context), **_pesquisa(owner_org))

    assert _groups(dataset) == [("implementacao_bncc", "Implementação da BNCC")]
    group = call_action("group_show", id="implementacao_bncc", include_datasets=True)
    assert [package["name"] for package in group["packages"]] == [dataset["name"]]


def test_tema_change_moves_dataset_between_groups(editor_context):
    context, owner_org = editor_context
    dataset = call_action("package_create", context=dict(context), **_pesquisa(owner_org))

    patched = call_action(
        "package_patch", context=dict(context), id=dataset["id"], tema="ensino_aprendizagem"
    )

    assert _groups(patched) == [("ensino_aprendizagem", "Ensino e Aprendizagem")]
    assert call_action("group_show", id="implementacao_bncc")["package_count"] == 0


def test_update_keeps_tema_group_and_manual_category(editor_context):
    context, owner_org = editor_context
    factories.Group(name="curriculo", title="Currículo")
    dataset = call_action("package_create", context=dict(context), **_pesquisa(owner_org))
    call_action(
        "member_create",
        context={"user": factories.Sysadmin()["name"]},
        id="curriculo",
        object=dataset["id"],
        object_type="package",
        capacity="public",
    )

    patched = call_action("package_patch", context=dict(context), id=dataset["id"], title="Outro")
    moved = call_action(
        "package_patch", context=dict(context), id=dataset["id"], tema="politicas_educacionais"
    )

    assert sorted(_groups(patched)) == [
        ("curriculo", "Currículo"),
        ("implementacao_bncc", "Implementação da BNCC"),
    ]
    assert sorted(_groups(moved)) == [
        ("curriculo", "Currículo"),
        ("politicas_educacionais", "Políticas Educacionais"),
    ]


def test_existing_tema_group_is_reused(editor_context):
    context, owner_org = editor_context
    call_action("package_create", context=dict(context), **_pesquisa(owner_org))

    call_action(
        "package_create", context=dict(context), **_pesquisa(owner_org, name="mpb-pesquisa-2")
    )

    assert call_action("group_list") == ["implementacao_bncc"]
    assert call_action("group_show", id="implementacao_bncc")["package_count"] == 2
