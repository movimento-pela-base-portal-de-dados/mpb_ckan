import datetime

import ckan.model as model
import pytest
from ckan.plugins import toolkit
from ckan.tests import factories
from flask import session
from flask_login import login_user

from ckanext.mpb import first_login

pytestmark = pytest.mark.usefixtures("clean_db", "with_plugins")


def _user(last_active=None):
    user = model.User.get(factories.User()["name"])
    user.last_active = last_active
    return user


def test_first_login_redirects_once_to_profile_edit(app):
    user = _user()
    with app.flask_app.test_request_context():
        login_user(user)
        first_login.mark_first_login(app.flask_app, user=user)

        response = first_login.redirect_first_login()

        assert response.status_code == 302
        assert response.location.endswith(toolkit.url_for("user.edit", id=user.name))
        assert first_login.redirect_first_login() is None


def test_returning_user_is_not_redirected(app):
    user = _user(last_active=datetime.datetime.utcnow())
    with app.flask_app.test_request_context():
        login_user(user)
        first_login.mark_first_login(app.flask_app, user=user)

        assert first_login.SESSION_KEY not in session
        assert first_login.redirect_first_login() is None


def test_login_page_has_no_password_reset_link(app):
    response = app.get(toolkit.url_for("user.login"))

    assert toolkit.url_for("user.request_reset") not in response.body
