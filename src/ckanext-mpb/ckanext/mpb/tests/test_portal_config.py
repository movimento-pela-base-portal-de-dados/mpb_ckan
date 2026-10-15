from pathlib import Path

import pytest

import ckan.model as model
import ckan.plugins.toolkit as toolkit
from ckan.tests import factories, helpers


REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
ENV_EXAMPLE = REPOSITORY_ROOT / ".env.example"

pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "mpb activity"),
    pytest.mark.usefixtures("with_plugins"),
]


def _env_example():
    values = {}
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"')
    return values


def _auth_config():
    return {
        key.lower().replace("__", "."): toolkit.asbool(value)
        for key, value in _env_example().items()
        if key.startswith("CKAN__AUTH__")
    }


@pytest.fixture
def clean_db(with_plugins, reset_db, migrate_db_for):
    reset_db()
    migrate_db_for("activity")


@pytest.fixture
def portal_auth(ckan_config, monkeypatch):
    for key, value in _auth_config().items():
        monkeypatch.setitem(ckan_config, key, value)


def _assert_denied(action, user, **data_dict):
    context = {"user": user["name"] if user else "", "model": model}
    with pytest.raises(toolkit.NotAuthorized):
        helpers.call_auth(action, context, **data_dict)


def test_env_example_enables_portal_plugins():
    plugins = _env_example()["CKAN__PLUGINS"].split()

    assert {"mpb", "scheming_datasets", "activity", "pdf_view"} <= set(plugins)
    assert plugins[-1] == "envvars"


def test_env_example_restricts_auth_defaults():
    assert _auth_config() == {
        "ckan.auth.anon_create_dataset": False,
        "ckan.auth.create_unowned_dataset": False,
        "ckan.auth.create_dataset_if_not_in_organization": False,
        "ckan.auth.user_create_organizations": False,
        "ckan.auth.user_delete_organizations": False,
        "ckan.auth.user_create_groups": False,
        "ckan.auth.user_delete_groups": False,
        "ckan.auth.create_user_via_web": False,
        "ckan.auth.create_user_via_api": False,
        "ckan.auth.public_user_details": False,
        "ckan.auth.public_activity_stream_detail": False,
    }


@pytest.mark.usefixtures("clean_db", "portal_auth")
class TestPortalAuthorization:
    def test_anonymous_cannot_create_datasets_or_users(self):
        _assert_denied("package_create", None, name="mpb-anon")
        _assert_denied("user_create", None, name="mpb-anon")

    def test_user_outside_organization_cannot_create_dataset(self):
        _assert_denied("package_create", factories.User(), name="mpb-outsider")

    def test_organization_editor_can_create_dataset(self):
        editor = factories.User()
        organization = factories.Organization(
            users=[{"name": editor["name"], "capacity": "editor"}]
        )
        context = {"user": editor["name"], "model": model}

        assert helpers.call_auth(
            "package_create", context, name="mpb-editor", owner_org=organization["id"]
        )

    def test_users_cannot_create_organizations_or_groups(self):
        user = factories.User()

        _assert_denied("organization_create", user, name="mpb-org")
        _assert_denied("group_create", user, name="mpb-group")

    def test_admins_cannot_delete_organizations_or_groups(self):
        admin = factories.User()
        organization = factories.Organization(user=admin)
        group = factories.Group(user=admin)

        _assert_denied("organization_delete", admin, id=organization["id"])
        _assert_denied("group_delete", admin, id=group["id"])

    def test_anonymous_cannot_read_user_details(self):
        user = factories.User()

        _assert_denied("user_list", None)
        _assert_denied("user_show", None, id=user["id"])


@pytest.mark.usefixtures("clean_db")
def test_activity_stream_records_dataset_changes():
    dataset = factories.Dataset(user=factories.User())

    activities = helpers.call_action("package_activity_list", id=dataset["id"])

    assert [activity["activity_type"] for activity in activities] == ["new package"]
