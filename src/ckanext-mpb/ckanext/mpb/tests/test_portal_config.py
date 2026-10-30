import pytest

import ckan.model as model
import ckan.plugins.toolkit as toolkit
from ckan.tests import factories, helpers

from ckanext.mpb import constants


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "mpb activity"),
    pytest.mark.usefixtures("with_plugins"),
]


@pytest.fixture
def clean_db(with_plugins, reset_db, migrate_db_for):
    reset_db()
    migrate_db_for("activity")


def _assert_denied(action, user, **data_dict):
    context = {"user": user["name"] if user else "", "model": model}
    with pytest.raises(toolkit.NotAuthorized):
        helpers.call_auth(action, context, **data_dict)


def test_env_example_enables_portal_plugins(env_example):
    plugins = env_example["CKAN__PLUGINS"].split()

    assert {"mpb", "scheming_datasets", "activity", "pdf_view"} <= set(plugins)
    assert plugins[-1] == "envvars"


def test_env_example_offers_only_portuguese(env_example):
    assert env_example["CKAN__LOCALE_DEFAULT"] == "pt_BR"
    assert env_example["CKAN__LOCALES_OFFERED"] == "pt_BR"
    assert env_example["CKAN__DISPLAY_TIMEZONE"] == "America/Sao_Paulo"


def test_env_example_restricts_auth_defaults(auth_config):
    assert auth_config == {
        "ckan.auth.anon_create_dataset": False,
        "ckan.auth.create_unowned_dataset": False,
        "ckan.auth.create_dataset_if_not_in_organization": False,
        "ckan.auth.user_create_organizations": False,
        "ckan.auth.user_delete_organizations": False,
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

    def test_mpb_editor_can_create_group(self):
        editor = factories.User()
        factories.Organization(
            name=constants.DEFAULT_ORGANIZATION_NAME,
            users=[{"name": editor["name"], "capacity": "editor"}],
        )
        context = {"user": editor["name"], "model": model}

        assert helpers.call_auth("group_create", context, name="mpb-categoria")

    def test_only_mpb_editors_can_create_group(self):
        member = factories.User()
        pipeline_user = factories.User(name=constants.DEFAULT_PIPELINE_USER_NAME)
        partner_editor = factories.User()
        factories.Organization(
            name=constants.DEFAULT_ORGANIZATION_NAME,
            users=[
                {"name": member["name"], "capacity": "member"},
                {"name": pipeline_user["name"], "capacity": "editor"},
            ],
        )
        factories.Organization(users=[{"name": partner_editor["name"], "capacity": "editor"}])

        _assert_denied("group_create", member, name="mpb-categoria")
        _assert_denied("group_create", pipeline_user, name="mpb-categoria")
        _assert_denied("group_create", partner_editor, name="mpb-categoria")

    def test_group_creator_adds_dataset_and_pipeline_update_keeps_it(self):
        editor = factories.User()
        pipeline_user = factories.User(name=constants.DEFAULT_PIPELINE_USER_NAME)
        organization = factories.Organization(
            name=constants.DEFAULT_ORGANIZATION_NAME,
            users=[
                {"name": editor["name"], "capacity": "editor"},
                {"name": pipeline_user["name"], "capacity": "editor"},
            ],
        )
        dataset = factories.Dataset(owner_org=organization["id"])
        group = helpers.call_action("group_create", {"user": editor["name"]}, name="mpb-categoria")
        helpers.call_action(
            "member_create",
            {"user": editor["name"]},
            id=group["id"],
            object=dataset["id"],
            object_type="package",
            capacity="public",
        )

        updated = helpers.call_action(
            "package_update",
            {"user": pipeline_user["name"]},
            id=dataset["id"],
            name=dataset["name"],
            owner_org=organization["id"],
            title="Título atualizado pela carga",
        )

        assert updated["title"] == "Título atualizado pela carga"
        assert [group["name"] for group in updated["groups"]] == ["mpb-categoria"]

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


def test_footer_has_no_language_selector(app):
    response = app.get("/")

    assert 'id="field-lang-select"' not in response.body


def test_about_page_shows_portal_default(app):
    response = app.get(toolkit.url_for("home.about"))

    assert constants.PORTAL_DEFAULTS["ckan.site_about"] in response.body


@pytest.mark.usefixtures("clean_db")
def test_sysadmin_text_replaces_portal_default(app):
    sysadmin = factories.Sysadmin()
    helpers.call_action(
        "config_option_update",
        {"user": sysadmin["name"]},
        **{"ckan.site_about": "Texto definido pela administração"},
    )

    response = app.get(toolkit.url_for("home.about"))

    assert "Texto definido pela administração" in response.body
    assert constants.PORTAL_DEFAULTS["ckan.site_about"] not in response.body
