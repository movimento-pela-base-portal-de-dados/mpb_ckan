import secrets

import click

import ckan.plugins.toolkit as toolkit


PIPELINE_USER_CAPACITY = "editor"


@click.group(short_help="Comandos do Portal de Dados Movimento pela Base.")
def mpb():
    pass


@mpb.command("setup-portal")
def setup_portal():
    """Cria a organização do portal e o usuário de serviço das pipelines."""
    email = toolkit.config.get("ckanext.mpb.pipeline_user.email")
    if not email:
        raise click.ClickException(
            "Defina ckanext.mpb.pipeline_user.email (CKANEXT__MPB__PIPELINE_USER__EMAIL)."
        )

    site_user = toolkit.get_action("get_site_user")({"ignore_auth": True}, {})
    context = {"user": site_user["name"], "ignore_auth": True}

    organization = ensure_organization(
        context,
        toolkit.config.get("ckanext.mpb.organization.name"),
        toolkit.config.get("ckanext.mpb.organization.title"),
    )
    user = ensure_user(
        context, toolkit.config.get("ckanext.mpb.pipeline_user.name"), email
    )
    ensure_membership(context, organization, user, PIPELINE_USER_CAPACITY)

    click.secho(
        f"Usuário {user['name']} é {PIPELINE_USER_CAPACITY} da organização "
        f"{organization['name']}.",
        fg="green",
    )


def ensure_organization(context, name, title):
    try:
        return toolkit.get_action("organization_show")(dict(context), {"id": name})
    except toolkit.ObjectNotFound:
        return toolkit.get_action("organization_create")(
            dict(context), {"name": name, "title": title}
        )


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
