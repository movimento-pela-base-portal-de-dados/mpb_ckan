"""
Tests for plugin.py.

Tests are written using the pytest library (https://docs.pytest.org), and you
should read the testing guidelines in the CKAN docs:
https://docs.ckan.org/en/2.9/contributing/testing.html

To write tests for your extension you should install the pytest-ckan package:

    pip install pytest-ckan

This will allow you to use CKAN specific fixtures on your tests.

For instance, if your test involves database access you can use `clean_db` to
reset the database:

    import pytest

    from ckan.tests import factories

    @pytest.mark.usefixtures("clean_db")
    def test_some_action():

        dataset = factories.Dataset()

        # ...

For functional tests that involve requests to the application, you can use the
`app` fixture:

    from ckan.plugins import toolkit

    def test_some_endpoint(app):

        url = toolkit.url_for('myblueprint.some_endpoint')

        response = app.get(url)

        assert response.status_code == 200


To temporary patch the CKAN configuration for the duration of a test you can use:

    import pytest

    @pytest.mark.ckan_config("ckanext.myext.some_key", "some_value")
    def test_some_action():
        pass
"""

import re
from pathlib import Path

import pytest
from ckan.plugins import plugin_loaded

import ckanext.mpb.plugin as plugin
from ckanext.mpb import constants, theme


@pytest.mark.ckan_config("ckan.plugins", "mpb")
@pytest.mark.usefixtures("with_plugins")
def test_plugin():
    assert plugin_loaded("mpb")


def test_plugin_registers_theme_resources(monkeypatch):
    calls = []

    monkeypatch.setattr(
        plugin.toolkit,
        "add_template_directory",
        lambda config, directory: calls.append(("templates", config, directory)),
    )
    monkeypatch.setattr(
        plugin.toolkit,
        "add_public_directory",
        lambda config, directory: calls.append(("public", config, directory)),
    )
    monkeypatch.setattr(
        plugin.toolkit,
        "add_resource",
        lambda directory, name: calls.append(("resource", directory, name)),
    )
    monkeypatch.setattr(
        plugin.theme,
        "register_core_theme",
        lambda: calls.append(("theme",)),
    )

    config = {}
    plugin.MpbPlugin().update_config(config)

    assert calls == [
        ("templates", config, "templates"),
        ("public", config, "public"),
        ("resource", "assets", "mpb"),
        ("theme",),
    ]


@pytest.mark.ckan_config("ckan.plugins", "mpb")
@pytest.mark.usefixtures("with_plugins")
def test_home_page_uses_portal_assets_and_texts(app):
    body = app.get("/").body

    assert "ckanext-mpb/" in body and "-mpb.css" in body
    assert 'href="/custom.css"' not in body
    assert 'placeholder="Ex.: matrículas no ensino médio"' in body


def test_portal_defaults_replace_ckan_defaults():
    config = {
        "ckan.site_title": "CKAN",
        "ckan.site_logo": "/base/images/ckan-logo.png",
    }

    plugin.apply_portal_defaults(config)

    assert config == constants.PORTAL_DEFAULTS


def test_portal_defaults_fill_missing_options():
    config = {}

    plugin.apply_portal_defaults(config)

    assert config == constants.PORTAL_DEFAULTS


def test_portal_defaults_keep_configured_values():
    configured = {
        "ckan.site_title": "Portal de Homologação",
        "ckan.site_logo": "/logo-mpb.svg",
        "ckan.site_description": "Descrição de homologação",
        "ckan.site_about": "Sobre o portal de homologação",
        "licenses_group_url": "file:///etc/ckan/licenses.json",
    }
    config = dict(configured)

    plugin.apply_portal_defaults(config)

    assert config == configured


@pytest.mark.ckan_config("ckan.plugins", "mpb")
@pytest.mark.usefixtures("with_plugins")
def test_css_fonts_are_served_locally(app):
    css = (Path(plugin.__file__).parent / "assets" / "css" / "typography.css").read_text()
    fonts = re.findall(r'url\("(/fonts/[^"]+\.woff2)"\)', css)

    assert {"Source Serif Pro", "Open Sans"} <= set(re.findall(r'font-family: "([^"]+)"', css))
    assert fonts
    for font in fonts:
        assert app.get(font).status_code == 200


def test_core_rem_values_follow_10px_root():
    css = ".a{font-size:.875rem;padding:0.5rem 1rem;width:calc(1.375rem + 1.5vw)}.x2rem{}"

    assert theme.scale_rem(css) == (
        ".a{font-size:1.4rem;padding:0.8rem 1.6rem;width:calc(2.2rem + 1.5vw)}.x2rem{}"
    )


def test_core_theme_is_scaled(app):
    body = app.get("/").get_data(as_text=True)
    href = re.search(r'href="(/webassets/base/[^"]*main\.css)"', body).group(1)

    assert "--bs-body-font-size: 1.4rem" in app.get(href).get_data(as_text=True)
