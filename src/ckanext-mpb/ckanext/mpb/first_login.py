import ckan.plugins.toolkit as toolkit
from flask import session

SESSION_KEY = "mpb_first_login"
NOTICE = "Este é o seu primeiro acesso. Troque a senha provisória por uma senha sua."


def mark_first_login(sender, user=None, **kwargs):
    if user is not None and user.last_active is None:
        session[SESSION_KEY] = True


def redirect_first_login():
    if not session.pop(SESSION_KEY, False) or not toolkit.current_user.is_authenticated:
        return None
    toolkit.h.flash_notice(NOTICE)
    return toolkit.redirect_to("user.edit", id=toolkit.current_user.name)
