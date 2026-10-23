from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.app_manager.classes import (
    CommandArgument, InitializationStep
)
from mayan.apps.app_manager.literals import (
    PROCESS_INITIAL_SETUP, PROCESS_UPGRADE
)
from mayan.apps.app_manager.runlevels import (
    runlevel_database, runlevel_preparation
)
from mayan.apps.templating.classes import AJAXTemplate

from .initializers import (
    initializer_create_media_storage,
    initializer_create_upload_temporary_folder,
    initializer_create_user_settings_folder,
    initializer_initial_setup_migrate, initializer_upgrade_migrate,
    initializer_verify_secret_key
)
from .links import (
    link_about, link_knowledge_base, link_license, link_separator_information,
    link_setup, link_support, link_tools, link_trademark_policy
)
from .menus import menu_system, menu_topbar, menu_user
from .settings import setting_home_view


class CommonApp(MayanAppConfig):
    app_namespace = 'common'
    app_url = ''
    has_rest_api = True
    has_tests = True
    name = 'mayan.apps.common'
    static_media_ignore_patterns = (
        'mptt/*',
    )
    verbose_name = _(message='Common')

    def ready(self):
        super().ready()

        AJAXTemplate(
            name='menu_main', template_name='appearance/menus/main.html'
        )
        AJAXTemplate(
            context={'home_view': setting_home_view.value},
            name='menu_topbar',
            template_name='appearance/menus/topbar.html'
        )

        InitializationStep(
            arguments=(
                CommandArgument(
                    '--force', action='store_true', dest='force',
                    help='Force execution of the initialization process.'
                ),
            ), fatal=True, function=initializer_create_media_storage,
            label=_(message='Create the media storage folder'),
            order=0, name='common.create_media_storage',
            process=PROCESS_INITIAL_SETUP, runlevel=runlevel_preparation
        )
        InitializationStep(
            fatal=True, function=initializer_verify_secret_key,
            label=_(message='Verify the secret key'),
            name='common.verify_secret_key', order=10,
            process=PROCESS_INITIAL_SETUP, runlevel=runlevel_preparation
        )

        InitializationStep(
            fatal=True, function=initializer_initial_setup_migrate,
            label=_(message='Apply database migrations'),
            name='common.initial_setup_migrate',
            process=PROCESS_INITIAL_SETUP, runlevel=runlevel_database
        )
        InitializationStep(
            fatal=True, function=initializer_upgrade_migrate,
            label=_(message='Apply database migrations'),
            name='common.upgrade_migrate', process=PROCESS_UPGRADE,
            runlevel=runlevel_database
        )
        InitializationStep(
            function=initializer_create_user_settings_folder,
            label=_(message='Create the user settings folder'),
            name='common.upgrade_create_user_settings_folder',
            process=PROCESS_UPGRADE, runlevel=runlevel_preparation
        )
        InitializationStep(
            function=initializer_create_upload_temporary_folder,
            label=_(message='Create the upload temporary folder'),
            name='common.upgrade_create_upload_temporary_folder',
            process=PROCESS_UPGRADE, runlevel=runlevel_preparation
        )

        menu_system.bind_links(
            links=(
                link_tools, link_setup, link_separator_information,
                link_knowledge_base, link_support, link_about, link_license
            )
        )
        menu_system.bind_links(
            links=(link_trademark_policy,), position=8
        )
        menu_topbar.bind_links(
            links=(menu_system, menu_user),
            position=10
        )
