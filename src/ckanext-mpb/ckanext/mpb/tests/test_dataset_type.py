import pytest

import ckan.plugins.toolkit as toolkit
from ckan.tests import factories
from ckan.tests.helpers import call_action

from ckanext.mpb.tests.test_schema import SCHEMA_OPTION, _pesquisa


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "mpb scheming_datasets"),
    pytest.mark.ckan_config("scheming.dataset_schemas", SCHEMA_OPTION),
    pytest.mark.ckan_config("ckan.default.package_type", "pesquisa"),
    pytest.mark.usefixtures("with_plugins", "clean_db"),
]


def _context(user):
    return {"user": user["name"], "ignore_auth": False}


@pytest.mark.parametrize("user_factory", [factories.Sysadmin, factories.User])
def test_dataset_type_cannot_be_created(user_factory):
    user = user_factory()
    organization = factories.Organization(
        users=[{"name": user["name"], "capacity": "editor"}]
    )

    with pytest.raises(toolkit.NotAuthorized):
        call_action(
            "package_create",
            context=_context(user),
            type="dataset",
            name="mpb-dataset",
            owner_org=organization["id"],
        )


def test_package_without_type_is_rejected():
    sysadmin = factories.Sysadmin()
    organization = factories.Organization()
    payload = _pesquisa(organization["id"])
    del payload["type"]

    with pytest.raises(toolkit.NotAuthorized):
        call_action("package_create", context=_context(sysadmin), **payload)


def test_pesquisa_can_be_created():
    sysadmin = factories.Sysadmin()
    organization = factories.Organization()

    created = call_action(
        "package_create", context=_context(sysadmin), **_pesquisa(organization["id"])
    )

    assert created["type"] == "pesquisa"


def test_dataset_form_is_blocked_and_pesquisa_form_is_open(app):
    sysadmin = factories.SysadminWithToken()
    headers = {"Authorization": sysadmin["token"]}

    assert app.get("/dataset/new", headers=headers).status_code == 403
    assert app.get("/pesquisa/new", headers=headers).status_code == 200
