import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.mpb import cli
from ckanext.mpb import constants as c


def apply_portal_defaults(config_):
    for key, value in c.PORTAL_DEFAULTS.items():
        if config_.get(key) in (None, c.CKAN_DEFAULTS[key]):
            config_[key] = value


class MpbPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigDeclaration)
    plugins.implements(plugins.IClick)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "mpb")
        apply_portal_defaults(config_)

    # IConfigDeclaration

    def declare_config_options(self, declaration, key):
        declaration.annotate("ckanext-mpb")
        declaration.declare(c.ORGANIZATION_NAME, c.DEFAULT_ORGANIZATION_NAME)
        declaration.declare(c.ORGANIZATION_TITLE, c.DEFAULT_ORGANIZATION_TITLE)
        declaration.declare(c.PIPELINE_USER_NAME, c.DEFAULT_PIPELINE_USER_NAME)
        declaration.declare(c.PIPELINE_USER_EMAIL)

    # IClick

    def get_commands(self):
        return cli.get_commands()
