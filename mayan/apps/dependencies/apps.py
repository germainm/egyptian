from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.app_manager.classes import (
    CommandArgument, InitializationStep
)
from mayan.apps.app_manager.literals import (
    PROCESS_INITIAL_SETUP, PROCESS_UPGRADE
)
from mayan.apps.app_manager.runlevels import runlevel_dependencies
from mayan.apps.common.menus import (
    menu_list_facet, menu_return, menu_system, menu_tools
)
from mayan.apps.forms import column_widgets
from mayan.apps.navigation.source_columns import SourceColumn

from .classes import Dependency, DependencyGroup, DependencyGroupEntry
from .initializers import initializer_dependencies_install
from .links import (
    link_check_version, link_dependency_group_entry_detail,
    link_dependency_group_entry_list, link_dependency_group_list,
    link_packages_licenses, link_dependency_tool
)


class DependenciesApp(MayanAppConfig):
    app_namespace = 'dependencies'
    app_url = 'dependencies'
    has_rest_api = False
    has_tests = True
    name = 'mayan.apps.dependencies'
    verbose_name = _(message='Dependencies')

    def ready(self):
        super().ready()

        Dependency.load_modules()

        InitializationStep(
            arguments=(
                CommandArgument(
                    '--no-dependencies', shared=True, action='store_true',
                    dest='no_dependencies',
                    help='Don\'t install dependencies.'
                ),
            ), function=initializer_dependencies_install,
            label=_(message='Install dependencies'),
            name='dependencies.install', order=0,
            process=(PROCESS_INITIAL_SETUP, PROCESS_UPGRADE),
            runlevel=runlevel_dependencies
        )

        SourceColumn(
            attribute='get_label', is_identifier=True, label=_(message='Label'),
            order=-1, source=Dependency
        )
        SourceColumn(
            attribute='name', include_label=True, label=_(message='Internal name'),
            order=0, source=Dependency
        )
        SourceColumn(
            attribute='get_help_text', include_label=True,
            label=_(message='Description'), order=1, source=Dependency
        )
        SourceColumn(
            attribute='class_name_verbose_name', include_label=True,
            label=_(message='Type'), order=2, source=Dependency
        )
        SourceColumn(
            attribute='get_other_data', include_label=True,
            label=_(message='Other data'), order=3, source=Dependency
        )
        SourceColumn(
            attribute='app_label_verbose_name', include_label=True,
            label=_(message='Declared by'), order=4, source=Dependency
        )
        SourceColumn(
            attribute='get_version_string', include_label=True,
            label=_(message='Version'), order=5, source=Dependency
        )
        SourceColumn(
            attribute='get_environments_verbose_name', include_label=True,
            label=_(message='Environments'), order=6, source=Dependency
        )
        SourceColumn(
            attribute='check', include_label=True, label=_(message='Check'), order=7,
            source=Dependency, widget=column_widgets.TwoStateWidget
        )

        SourceColumn(
            attribute='label', is_identifier=True, label=_(message='Label'),
            order=0, source=DependencyGroup
        )
        SourceColumn(
            attribute='help_text', include_label=True,
            label=_(message='Description'), order=1, source=DependencyGroup
        )

        SourceColumn(
            attribute='label', is_identifier=True, label=_(message='Label'), order=0,
            source=DependencyGroupEntry
        )
        SourceColumn(
            attribute='help_text', include_label=True,
            label=_(message='Description'), order=1, source=DependencyGroupEntry
        )

        menu_system.bind_links(
            links=(link_packages_licenses,), position=7
        )
        menu_list_facet.bind_links(
            links=(link_dependency_group_entry_list,),
            sources=(DependencyGroup,)
        )
        menu_list_facet.bind_links(
            links=(link_dependency_group_entry_detail,),
            sources=(DependencyGroupEntry,)
        )
        menu_return.bind_links(
            links=(link_dependency_group_list,),
            sources=(
                DependencyGroup, 'dependencies:dependency_group_list'
            )
        )
        menu_tools.bind_links(
            links=(link_dependency_tool, link_check_version)
        )
