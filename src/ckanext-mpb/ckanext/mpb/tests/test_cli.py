import pytest

import ckan.model as model
import ckan.plugins.toolkit as toolkit
from ckan.tests import factories, helpers

from ckanext.mpb import constants
from ckanext.mpb.cli import mpb
from ckanext.mpb.plugin import MpbPlugin


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "mpb"),
    pytest.mark.usefixtures("with_plugins", "clean_db", "portal_setup_config"),
]


@pytest.fixture
def portal_setup_config(ckan_config, monkeypatch, env_example):
    for key, value in env_example.items():
        if key.startswith("CKANEXT__MPB__"):
            monkeypatch.setitem(ckan_config, key.lower().replace("__", "."), value)


@pytest.fixture
def setup_portal(cli):
    def run():
        result = cli.invoke(mpb, ["setup-portal"])
        assert result.exit_code == 0, result.output
        return result

    return run


def _pipeline_editors(organization_name):
    organization = helpers.call_action("organization_show", id=organization_name)
    members = helpers.call_action(
        "member_list", id=organization["id"], object_type="user", capacity="editor"
    )
    return [member_id for member_id, _, _ in members]


def test_plugin_registers_mpb_command():
    assert MpbPlugin().get_commands() == [mpb]


def test_env_example_defines_portal_setup(env_example):
    assert env_example["CKANEXT__MPB__ORGANIZATION__NAME"] == "movimento-pela-base"
    assert env_example["CKANEXT__MPB__PIPELINE_USER__NAME"] == "mpb-pipelines"
    assert env_example["CKANEXT__MPB__PIPELINE_USER__EMAIL"]


def test_setup_portal_creates_organization_and_pipeline_editor(setup_portal):
    setup_portal()

    organization = helpers.call_action("organization_show", id="movimento-pela-base")
    user = helpers.call_action("user_show", id="mpb-pipelines")

    assert organization["title"] == "Movimento pela Base"
    assert _pipeline_editors("movimento-pela-base") == [user["id"]]
    assert not user["sysadmin"]


def test_setup_portal_is_idempotent(setup_portal):
    setup_portal()
    setup_portal()

    assert helpers.call_action("organization_list") == ["movimento-pela-base"]
    assert len(_pipeline_editors("movimento-pela-base")) == 1


def test_setup_portal_restores_editor_role(setup_portal):
    setup_portal()
    helpers.call_action(
        "organization_member_create",
        id="movimento-pela-base",
        username="mpb-pipelines",
        role="admin",
    )

    setup_portal()

    user = helpers.call_action("user_show", id="mpb-pipelines")
    assert _pipeline_editors("movimento-pela-base") == [user["id"]]


def test_setup_portal_requires_pipeline_user_email(cli, ckan_config, monkeypatch):
    monkeypatch.setitem(ckan_config, constants.PIPELINE_USER_EMAIL, "")

    result = cli.invoke(mpb, ["setup-portal"])

    assert result.exit_code != 0
    assert "CKANEXT__MPB__PIPELINE_USER__EMAIL" in result.output
    assert helpers.call_action("organization_list") == []


@pytest.mark.usefixtures("portal_auth")
def test_pipeline_user_publishes_only_in_portal_organization(setup_portal):
    setup_portal()
    organization = helpers.call_action("organization_show", id="movimento-pela-base")
    other_organization = factories.Organization()
    context = {"user": "mpb-pipelines", "model": model}

    assert helpers.call_auth(
        "package_create", dict(context), name="mpb-pipeline", owner_org=organization["id"]
    )
    with pytest.raises(toolkit.NotAuthorized):
        helpers.call_auth(
            "package_create",
            dict(context),
            name="mpb-other",
            owner_org=other_organization["id"],
        )
    with pytest.raises(toolkit.NotAuthorized):
        helpers.call_auth("organization_create", dict(context), name="mpb-new-org")
