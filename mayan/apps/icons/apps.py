from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig


class IconsApp(MayanAppConfig):
    app_namespace = 'icons'
    app_url = 'icons'
    has_static_media = True
    name = 'mayan.apps.icons'
    static_media_ignore_patterns = (
        'icons/node_modules/@fortawesome/fontawesome-free/less/*',
        'icons/node_modules/@fortawesome/fontawesome-free/metadata/*',
        'icons/node_modules/@fortawesome/fontawesome-free/sprites/*',
        'icons/node_modules/@fortawesome/fontawesome-free/svgs/*',
        'icons/node_modules/@fortawesome/fontawesome-free/webfonts/*',
        'icons/node_modules/@fortawesome/fontawesome-free/css/all*',
        'icons/node_modules/@fortawesome/fontawesome-free/css/brands*',
        'icons/node_modules/@fortawesome/fontawesome-free/css/fontawesome*',
        'icons/node_modules/@fortawesome/fontawesome-free/css/regular*',
        'icons/node_modules/@fortawesome/fontawesome-free/css/solid*',
        'icons/node_modules/@fortawesome/fontawesome-free/css/svg-with-js.css',
        'icons/node_modules/@fortawesome/fontawesome-free/css/v4-font-face*',
        'icons/node_modules/@fortawesome/fontawesome-free/css/v4-shims*',
        'icons/node_modules/@fortawesome/fontawesome-free/css/v5-font-face*',
        'icons/node_modules/@fortawesome/fontawesome-free/js/all.js',
        'icons/node_modules/@fortawesome/fontawesome-free/js/brands*',
        'icons/node_modules/@fortawesome/fontawesome-free/js/conflict-detection*',
        'icons/node_modules/@fortawesome/fontawesome-free/js/fontawesome*',
        'icons/node_modules/@fortawesome/fontawesome-free/js/regular*',
        'icons/node_modules/@fortawesome/fontawesome-free/js/solid*',
        'icons/node_modules/@fortawesome/fontawesome-free/js/v4-shims*',
    )
    verbose_name = _(message='Icons')
