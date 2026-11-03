import json

import pytest

from ckan.tests import factories
from ckan.tests.helpers import call_action

from ckanext.mpb import privacy
from ckanext.mpb.tests.test_schema import SCHEMA_OPTION, _pesquisa


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "mpb scheming_datasets activity"),
    pytest.mark.ckan_config("scheming.dataset_schemas", SCHEMA_OPTION),
    pytest.mark.ckan_config("ckan.default.package_type", "pesquisa"),
    pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index"),
]

PRIVATE_URL = "https://example.org/relatorio-secreto.pdf"
PUBLIC_URL = "https://example.org/documento-publico.pdf"
SEARCH_TERM = "termoexclusivodebusca"
SECRETS = [
    "zirconio",
    "objetivo-secreto",
    "publico-secreto",
    "topico-secreto",
    "apoio-secreto",
    "realizacao-secreta",
    "titulo-alternativo-secreto",
    SEARCH_TERM,
    "relatorio-secreto",
]


@pytest.fixture
def clean_db(with_plugins, reset_db, migrate_db_for):
    reset_db()
    migrate_db_for("activity")


@pytest.fixture
def portal():
    member = factories.UserWithToken()
    editor = factories.UserWithToken()
    outsider = factories.UserWithToken()
    partner = factories.UserWithToken()
    sysadmin = factories.SysadminWithToken()
    organization = factories.Organization(
        users=[
            {"name": member["name"], "capacity": "member"},
            {"name": editor["name"], "capacity": "editor"},
        ]
    )
    factories.Organization(users=[{"name": partner["name"], "capacity": "member"}])
    dataset = call_action(
        "package_create",
        context={"user": sysadmin["name"]},
        **_pesquisa(
            organization["id"],
            notes="Resumo com a palavra zirconio.",
            objetivo="objetivo-secreto",
            publico=["publico-secreto"],
            topico=["topico-secreto"],
            apoio=["apoio-secreto"],
            realizacao=["realizacao-secreta"],
            titulo_alternativo="titulo-alternativo-secreto",
            termos_busca=[SEARCH_TERM],
            resources=[
                {
                    "url": PUBLIC_URL,
                    "name": "Documento",
                    "format": "PDF",
                    "tipo_documento": "documento",
                },
                {
                    "url": PRIVATE_URL,
                    "name": "Relatório",
                    "format": "PDF",
                    "tipo_documento": "relatorio",
                },
            ],
        ),
    )
    return {
        "dataset": dataset,
        "anonymous": None,
        "outsider": outsider,
        "partner": partner,
        "member": member,
        "editor": editor,
        "sysadmin": sysadmin,
    }


def _headers(user):
    return {"Authorization": user["token"]} if user else {}


def _get(app, portal, persona, path, status=200):
    response = app.get(path, headers=_headers(portal[persona]), status=status)
    return response.get_data(as_text=True)


def _api(app, portal, persona, action, status=200, **params):
    query = "&".join(
        f"{key}={json.dumps(value) if isinstance(value, list) else value}"
        for key, value in params.items()
    )
    return _get(app, portal, persona, f"/api/3/action/{action}?{query}", status)


def _assert_hidden(body):
    for secret in SECRETS:
        assert secret not in body


NON_MEMBERS = ["anonymous", "outsider", "partner"]
ORGANIZATION_USERS = ["member", "editor", "sysadmin"]


def test_schema_marks_private_fields_and_resource_types():
    assert privacy.private_fields() == {
        "notes",
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
    assert privacy.search_only_fields() == {"termos_busca"}
    assert privacy.public_resource_types() == {"documento"}


@pytest.mark.parametrize("persona", NON_MEMBERS)
def test_package_show_hides_private_fields_from_non_members(app, portal, persona):
    body = _api(app, portal, persona, "package_show", id=portal["dataset"]["name"])
    result = json.loads(body)["result"]

    _assert_hidden(body)
    assert result["title"] == "Pesquisa de teste"
    assert result["tema"] == "implementacao"
    assert [resource["url"] for resource in result["resources"]] == [PUBLIC_URL]
    assert result["num_resources"] == 1


@pytest.mark.parametrize("persona", ORGANIZATION_USERS)
def test_package_show_shows_private_fields_to_organization_users(app, portal, persona):
    body = _api(app, portal, persona, "package_show", id=portal["dataset"]["name"])
    result = json.loads(body)["result"]

    assert result["objetivo"] == "objetivo-secreto"
    assert result["termos_busca"] == [SEARCH_TERM]
    assert [resource["url"] for resource in result["resources"]] == [PUBLIC_URL, PRIVATE_URL]


def test_package_show_with_default_schema_hides_private_extras(app, portal):
    body = _api(
        app, portal, "anonymous", "package_show", id=portal["dataset"]["name"], use_default_schema="true"
    )

    _assert_hidden(body)


@pytest.mark.parametrize("persona", NON_MEMBERS)
def test_search_results_hide_private_fields(app, portal, persona):
    body = _api(app, portal, persona, "package_search", q="Pesquisa")

    assert json.loads(body)["result"]["count"] == 1
    _assert_hidden(body)


def test_search_results_show_private_fields_to_members(app, portal):
    body = _api(app, portal, "member", "package_search", q="Pesquisa")

    assert "objetivo-secreto" in body
    assert PRIVATE_URL in body


@pytest.mark.parametrize("persona", ["anonymous", "member"])
def test_private_text_is_not_searchable(app, portal, persona):
    for query in ["zirconio", "objetivo-secreto", 'res_url:"' + PRIVATE_URL + '"']:
        body = _api(app, portal, persona, "package_search", q=query)
        assert json.loads(body)["result"]["count"] == 0


def test_search_terms_find_the_dataset_without_being_shown(app, portal):
    body = _api(app, portal, "anonymous", "package_search", q=SEARCH_TERM)

    assert json.loads(body)["result"]["count"] == 1
    assert SEARCH_TERM not in body


@pytest.mark.parametrize(
    "fl", ["id,validated_data_dict,data_dict", "*", "id validated_data_dict", "notes,res_url"]
)
def test_search_field_list_cannot_expose_private_fields(app, portal, fl):
    body = _api(app, portal, "anonymous", "package_search", q="Pesquisa", fl=fl)

    _assert_hidden(body)


def test_search_facets_do_not_expose_private_fields(app, portal):
    body = _api(
        app,
        portal,
        "anonymous",
        "package_search",
        **{"facet.field": ["publico", "extras_publico", "res_url", "res_name", "text"]},
    )

    _assert_hidden(body)


def test_private_resource_is_blocked_for_non_members(app, portal):
    public_id, private_id = (resource["id"] for resource in portal["dataset"]["resources"])
    name = portal["dataset"]["name"]

    _api(app, portal, "anonymous", "resource_show", id=public_id)
    _api(app, portal, "anonymous", "resource_show", status=403, id=private_id)
    _api(app, portal, "outsider", "resource_show", status=403, id=private_id)
    _api(app, portal, "member", "resource_show", id=private_id)
    for path in [
        f"/pesquisa/{name}/resource/{private_id}",
        f"/dataset/{name}/resource/{private_id}/download",
    ]:
        assert app.get(path).status_code in (403, 404)


def test_resource_search_hides_private_resources(app, portal):
    def count(persona):
        body = _api(app, portal, persona, "resource_search", query="url:relatorio-secreto")
        return json.loads(body)["result"]["count"]

    assert count("anonymous") == 0
    assert count("outsider") == 0
    assert count("member") == 1


def test_dataset_page_hides_private_values(app, portal):
    path = f"/pesquisa/{portal['dataset']['name']}"

    _assert_hidden(_get(app, portal, "anonymous", path))
    assert "zirconio" in _get(app, portal, "member", path)


def test_editor_update_keeps_private_fields(app, portal):
    app.post(
        "/api/3/action/package_patch",
        json={"id": portal["dataset"]["id"], "title": "Título revisado"},
        headers=_headers(portal["editor"]),
    )

    body = _api(app, portal, "sysadmin", "package_show", id=portal["dataset"]["id"])
    result = json.loads(body)["result"]

    assert result["title"] == "Título revisado"
    assert result["objetivo"] == "objetivo-secreto"
    assert result["termos_busca"] == [SEARCH_TERM]
    assert len(result["resources"]) == 2


def test_followed_dataset_list_hides_private_fields(app, portal):
    outsider = portal["outsider"]
    call_action("follow_dataset", context={"user": outsider["name"]}, id=portal["dataset"]["id"])

    _assert_hidden(_api(app, portal, "outsider", "dataset_followee_list", id=outsider["name"]))


def test_activity_does_not_expose_private_fields(app, portal):
    dataset_id = portal["dataset"]["id"]

    for persona in NON_MEMBERS:
        _assert_hidden(_api(app, portal, persona, "package_activity_list", id=dataset_id))
        _assert_hidden(
            _api(app, portal, persona, "recently_changed_packages_activity_list")
        )
    activity_id = json.loads(
        _api(app, portal, "sysadmin", "package_activity_list", id=dataset_id)
    )["result"][0]["id"]
    _api(app, portal, "anonymous", "activity_data_show", status=403, id=activity_id)
    _api(app, portal, "member", "activity_data_show", status=403, id=activity_id)


@pytest.fixture
def uploads(portal, create_with_upload, ckan_config, monkeypatch, tmp_path):
    monkeypatch.setitem(ckan_config, "ckan.storage_path", str(tmp_path))
    context = {"user": portal["editor"]["name"], "ignore_auth": False}

    def upload(content, filename, tipo_documento):
        return create_with_upload(
            content,
            filename,
            package_id=portal["dataset"]["id"],
            name=filename,
            format="PDF",
            tipo_documento=tipo_documento,
            context=dict(context),
        )

    return {
        "public": [
            upload(b"documento publico 1", "documento-1.pdf", "documento"),
            upload(b"documento publico 2", "documento-2.pdf", "documento"),
        ],
        "private": upload(b"relatorio privado", "relatorio.pdf", "relatorio"),
    }


def _download(app, portal, persona, resource):
    path = resource["url"].split("://", 1)[-1].split("/", 1)[-1]
    return app.get(f"/{path}", headers=_headers(portal[persona]))


def test_uploaded_files_follow_resource_type(app, portal, uploads):
    for persona in ["anonymous", "member"]:
        for resource in uploads["public"]:
            response = _download(app, portal, persona, resource)
            assert response.status_code == 200
            assert response.get_data().startswith(b"documento publico")

    assert _download(app, portal, "anonymous", uploads["private"]).status_code == 403
    assert _download(app, portal, "outsider", uploads["private"]).status_code == 403
    assert _download(app, portal, "member", uploads["private"]).get_data() == b"relatorio privado"


def test_pipeline_patch_keeps_uploaded_files(app, portal, uploads):
    pipeline_user = factories.User()
    call_action(
        "member_create",
        id=portal["dataset"]["owner_org"],
        object=pipeline_user["name"],
        object_type="user",
        capacity="editor",
    )

    call_action(
        "package_patch",
        context={"user": pipeline_user["name"], "ignore_auth": False},
        id=portal["dataset"]["id"],
        title="Título atualizado pela carga",
    )

    resources = call_action("package_show", id=portal["dataset"]["id"])["resources"]
    assert len(resources) == 5
    assert sum(resource["url_type"] == "upload" for resource in resources) == 3
