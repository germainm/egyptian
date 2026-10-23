from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.app_manager.classes import (
    CommandArgument, InitializationStep
)
from mayan.apps.app_manager.literals import (
    PROCESS_INITIAL_SETUP, PROCESS_UPGRADE
)
from mayan.apps.app_manager.runlevels import runlevel_dependencies
from mayan.apps.common.menus import menu_list_facet, menu_topbar

from .classes import Theme
from .initializers import initializer_appearance_prepare_static
from .links import (
    link_ajax_refresh, link_user_current_theme_edit, link_user_theme_edit
)


class AppearanceApp(MayanAppConfig):
    app_namespace = 'appearance'
    app_url = 'appearance'
    has_javascript_translations = True
    has_rest_api = True
    has_static_media = True
    has_tests = True
    name = 'mayan.apps.appearance'
    static_media_ignore_patterns = (
        'AUTHORS*', 'CHANGE*', 'CONTRIBUT*', 'CODE_OF_CONDUCT*', 'Grunt*',
        'MAINTAIN*', 'README*', '*.less', '*.md', '*.nupkg', '*.nuspec',
        '*.scss*', '*.sh', '*tests*', 'bower*', 'composer.json*',
        'demo*', 'grunt*', 'gulp*', 'install', 'less', 'package.json*',
        'package-lock*', 'test', 'tests', 'variable*', '*.xcf',
        'appearance/node_modules/@fancyapps/fancybox/docs/*',
        'appearance/node_modules/@fancyapps/fancybox/src/*',
        'appearance/node_modules/bootswatch/docs/*',
        'appearance/node_modules/jquery/src/*',
        'appearance/node_modules/jquery-form/_config.yml',
        'appearance/node_modules/jquery-form/form.jquery.json',
        'appearance/node_modules/jquery-form/docs/*',
        'appearance/node_modules/jquery-form/src/*',
        'appearance/node_modules/select2/src/*',
        'appearance/node_modules/toastr/karma.conf.js',
        'appearance/node_modules/toastr/toastr.js',
        'appearance/node_modules/toastr/toastr-icon.png',
        'appearance/node_modules/toastr/nuget/*'
    )
    verbose_name = _(message='Appearance')

    def ready(self):
        super().ready()

        User = get_user_model()

        Theme.load_modules()

        InitializationStep(
            name='appearance.prepare_static',
            process=(PROCESS_INITIAL_SETUP, PROCESS_UPGRADE),
            runlevel=runlevel_dependencies,
            function=initializer_appearance_prepare_static, order=10,
            label=_(message='Collect static files'),
            arguments=(
                CommandArgument(
                    '--no-dependencies', shared=True, action='store_true',
                    dest='no_dependencies',
                    help='Don\'t install dependencies.'
                ),
            )
        )

        menu_list_facet.bind_links(
            links=(link_user_current_theme_edit, link_user_theme_edit),
            sources=(User,)
        )

        menu_topbar.bind_links(
            links=(link_ajax_refresh,)
        )
