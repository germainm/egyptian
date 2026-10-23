from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig

from mayan.apps.common.menus import menu_list_facet

from .classes import ColorMode
from .links import link_user_color_mode_edit, link_user_current_color_mode


class AppearanceBootstrapApp(MayanAppConfig):
    app_namespace = 'appearance_bootstrap'
    app_url = 'appearance_bootstrap'
    has_javascript_translations = True
    has_rest_api = True
    has_static_media = True
    has_tests = True
    name = 'mayan.apps.appearance_bootstrap'
    verbose_name = _(message='Appearance (Bootstrap)')

    def ready(self):
        super().ready()

        User = get_user_model()

        ColorMode.load_modules()

        menu_list_facet.bind_links(
            links=(link_user_color_mode_edit, link_user_current_color_mode),
            sources=(User,)
        )
