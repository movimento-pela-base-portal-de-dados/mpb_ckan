import mimetypes
import os
import re

from ckan.common import config
from ckan.lib import webassets_tools
from webassets import Bundle
from webassets.filter import Filter, register_filter

ROOT_SCALE = 1.6
CORE_THEME = "css/main"
mimetypes.add_type("font/woff2", ".woff2")

REM_VALUE = re.compile(r"(?<![\w.-])(\d*\.?\d+)rem\b")


def scale_rem(css):
    return REM_VALUE.sub(lambda m: f"{float(m.group(1)) * ROOT_SCALE:g}rem", css)


class RemScale(Filter):
    name = "mpb_rem_scale"

    def output(self, _in, out, **kw):
        out.write(scale_rem(_in.read()))


def core_css_path():
    public = config["ckan.base_public_folder"]
    lib = os.path.dirname(webassets_tools.__file__)
    return os.path.abspath(os.path.join(lib, "..", public, "base", "css", "main.css"))


def register_core_theme():
    if webassets_tools.is_registered(CORE_THEME):
        return
    register_filter(RemScale)
    webassets_tools.env.register(
        CORE_THEME,
        Bundle(
            core_css_path(),
            filters=["cssrewrite", RemScale.name],
            output="base/%(version)s_main.css",
            debug=False,
        ),
    )
