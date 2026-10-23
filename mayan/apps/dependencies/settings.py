from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .literals import (
    DEFAULT_DEPENDENCIES_GOOGLE_FONTS_URL,
    DEFAULT_DEPENDENCIES_NPM_REGISTRY_URL
)

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='Dependencies'), name='dependencies'
)

setting_google_fonts_url = setting_namespace.do_setting_add(
    default=DEFAULT_DEPENDENCIES_GOOGLE_FONTS_URL,
    global_name='DEPENDENCIES_GOOGLE_FONTS_URL', help_text=_(
        message='URL of the service used to obtain the Google font '
        'dependencies. Point this to a Google Fonts mirror to avoid '
        'reaching the public service on every installation. The mirror '
        'must serve the same stylesheet path and rewrite the font file '
        'URL of the stylesheet to itself, which is the normal behavior of '
        'font mirrors.'
    )
)

setting_npm_registry_url = setting_namespace.do_setting_add(
    default=DEFAULT_DEPENDENCIES_NPM_REGISTRY_URL,
    global_name='DEPENDENCIES_NPM_REGISTRY_URL', help_text=_(
        message='URL of the NPM registry used to obtain the JavaScript '
        'dependencies. Point this to a pull through mirror to avoid '
        'reaching the public registry on every installation. The mirror '
        'must rewrite the tarball URL of the package metadata to itself, '
        'which is the normal behavior of registry mirrors.'
    )
)
