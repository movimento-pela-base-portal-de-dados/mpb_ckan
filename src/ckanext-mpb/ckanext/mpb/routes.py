import ckan.plugins.toolkit as toolkit

from ckanext.mpb import constants as c

SEARCH_ENDPOINT = f"{c.DATASET_TYPE}.search"


def add_search_rule(sender, blueprint):
    if blueprint.name != c.DATASET_TYPE:
        return
    blueprint.deferred_functions.insert(
        0,
        lambda state: state.app.add_url_rule(
            c.SEARCH_PATH,
            SEARCH_ENDPOINT,
            defaults={"package_type": c.DATASET_TYPE},
            strict_slashes=False,
        ),
    )


def redirect_about_page():
    if toolkit.request.endpoint == "home.about":
        return toolkit.redirect_to(toolkit.url_for("home.index") + f"#{c.ABOUT_ANCHOR}")
    return None
