import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


PORTAL_DEFAULTS = {
    "ckan.site_title": "Portal de Dados Movimento pela Base",
    "ckan.site_logo": "",
}


CKAN_DEFAULTS = {
    "ckan.site_title": "CKAN",
    "ckan.site_logo": "/base/images/ckan-logo.png",
}


def apply_portal_defaults(config_):
    for key, value in PORTAL_DEFAULTS.items():
        if config_.get(key) in (None, CKAN_DEFAULTS[key]):
            config_[key] = value


class MpbPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "mpb")
        apply_portal_defaults(config_)
