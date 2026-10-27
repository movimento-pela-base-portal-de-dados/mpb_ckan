import secrets

import click
import yaml

import ckan.plugins.toolkit as toolkit

from ckanext.mpb import constants as c


@click.group(short_help="Comandos do Portal de Dados Movimento pela Base.")
def mpb():
    pass


@mpb.command("setup-portal")
def setup_portal():
    """Cria a organização do portal, o usuário de serviço das pipelines e o catálogo."""
    email = toolkit.config.get(c.PIPELINE_USER_EMAIL)
    if not email:
        raise click.ClickException(
            f"Defina {c.PIPELINE_USER_EMAIL} (CKANEXT__MPB__PIPELINE_USER__EMAIL)."
        )

    catalog = load_catalog(c.CATALOG_PATH)

    site_user = toolkit.get_action("get_site_user")({"ignore_auth": True}, {})
    context = {"user": site_user["name"], "ignore_auth": True}

    organization = ensure_group(
        context,
        "organization",
        {
            "name": toolkit.config.get(c.ORGANIZATION_NAME),
            "title": toolkit.config.get(c.ORGANIZATION_TITLE),
        },
    )
    user = ensure_user(context, toolkit.config.get(c.PIPELINE_USER_NAME), email)
    ensure_membership(context, organization, user, c.PIPELINE_USER_CAPACITY)

    click.secho(
        f"Usuário {user['name']} é {c.PIPELINE_USER_CAPACITY} da organização "
        f"{organization['name']}.",
        fg="green",
    )

    for group_type, key in (("organization", "organizations"), ("group", "groups")):
        for data in catalog[key]:
            ensure_group(context, group_type, data)
    click.secho(
        f"Catálogo: {len(catalog['organizations'])} organizações parceiras e "
        f"{len(catalog['groups'])} categorias.",
        fg="green",
    )


def load_catalog(path):
    with open(path, encoding="utf-8") as catalog_file:
        catalog = yaml.safe_load(catalog_file) or {}
    for key in ("organizations", "groups"):
        catalog[key] = catalog.get(key) or []
        for data in catalog[key]:
            if not data.get("name") or not data.get("title"):
                raise click.ClickException(f"{path}: cada item de {key} precisa de name e title.")
    return catalog


def ensure_group(context, group_type, data):
    try:
        return toolkit.get_action(f"{group_type}_show")(dict(context), {"id": data["name"]})
    except toolkit.ObjectNotFound:
        return toolkit.get_action(f"{group_type}_create")(dict(context), dict(data))


def ensure_user(context, name, email):
    try:
        return toolkit.get_action("user_show")(dict(context), {"id": name})
    except toolkit.ObjectNotFound:
        return toolkit.get_action("user_create")(
            dict(context),
            {"name": name, "email": email, "password": secrets.token_urlsafe(32)},
        )


def ensure_membership(context, organization, user, capacity):
    members = toolkit.get_action("member_list")(
        dict(context),
        {"id": organization["id"], "object_type": "user", "capacity": capacity},
    )
    if any(member_id == user["id"] for member_id, _, _ in members):
        return
    toolkit.get_action("organization_member_create")(
        dict(context),
        {"id": organization["id"], "username": user["name"], "role": capacity},
    )


def get_commands():
    return [mpb]
