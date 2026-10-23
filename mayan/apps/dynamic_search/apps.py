from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.classes import ModelPermission
from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.app_manager.classes import InitializationStep
from mayan.apps.app_manager.literals import (
    PROCESS_INITIAL_SETUP, PROCESS_UPGRADE
)
from mayan.apps.app_manager.runlevels import (
    runlevel_bootstrap, runlevel_maintenance
)
from mayan.apps.common.menus import (
    menu_facet, menu_list_facet, menu_object, menu_return, menu_secondary,
    menu_tools
)
from mayan.apps.navigation.source_columns import SourceColumn

from .initializers import (
    initializer_search_backend_initialize, initializer_search_backend_upgrade
)
from .links import (
    link_saved_resultset_delete_single, link_saved_resultset_list,
    link_search, link_saved_resultset_result_list, link_search_advanced,
    link_search_again, link_search_backend_reindex,
    link_search_model_detail, link_search_model_list
)
from .permissions import (
    permission_saved_resultset_delete, permission_saved_resultset_view
)
from .search_backends import SearchBackend
from .search_fields import SearchField
from .search_models import SearchModel


class DynamicSearchApp(MayanAppConfig):
    app_namespace = 'search'
    app_url = 'search'
    has_rest_api = True
    has_tests = True
    name = 'mayan.apps.dynamic_search'
    verbose_name = _(message='Dynamic search')

    def ready(self):
        super().ready()

        SearchModel.load_modules()
        SearchBackend._enable()

        SavedResultset = self.get_model(model_name='SavedResultset')

        InitializationStep(
            function=initializer_search_backend_initialize,
            label=_(message='Initialize the search engine'),
            name='dynamic_search.search_backend_initialize',
            order=20, process=PROCESS_INITIAL_SETUP,
            runlevel=runlevel_bootstrap
        )

        InitializationStep(
            function=initializer_search_backend_upgrade,
            label=_(message='Upgrade the search engine'),
            name='dynamic_search.search_backend_upgrade',
            process=PROCESS_UPGRADE, runlevel=runlevel_maintenance,
        )

        ModelPermission.register(
            model=SavedResultset,
            permissions=(
                permission_saved_resultset_delete,
                permission_saved_resultset_view,
            )
        )

        SourceColumn(
            attribute='timestamp', is_identifier=True, is_sortable=True,
            source=SavedResultset
        )
        SourceColumn(
            attribute='user', include_label=True, is_sortable=True,
            source=SavedResultset
        )
        SourceColumn(
            attribute='app_label', include_label=True, source=SavedResultset
        )
        SourceColumn(
            attribute='model_name', include_label=True, source=SavedResultset
        )
        SourceColumn(
            attribute='result_count', include_label=True,
            source=SavedResultset
        )
        SourceColumn(
            attribute='search_explainer_text', include_label=True,
            source=SavedResultset
        )
        SourceColumn(
            attribute='time_to_live', include_label=True,
            source=SavedResultset
        )


        SourceColumn(
            attribute='label', help_text=_(
                message='The underlying database model whose content is '
                'indexed for search.'
            ), label=_(message='Model'), include_label=True,
            is_identifier=True, source=SearchModel
        )
        SourceColumn(
            attribute='full_name', help_text=_(
                message='The unique name used to reference the search model.'
            ), include_label=True, source=SearchModel
        )


        SourceColumn(
            attribute='label', help_text=_(
                message='The underlying database field whose content is '
                'indexed for search.'
            ), include_label=True, is_identifier=True,
            label=_(message='Field'), source=SearchField
        )
        SourceColumn(
            attribute='field_name', include_label=True, source=SearchField
        )
        SourceColumn(
            attribute='get_search_field_class_label', include_label=True,
            source=SearchField
        )
        SourceColumn(
            attribute='field_class_label', help_text=_(
                message='The underlying database field type. This '
                'determines the kind of data that is stored in the '
                'database.'
            ), label=_(message='Field class'), include_label=True,
            source=SearchField
        )
        SourceColumn(
            attribute='get_help_text', label=_(message='Description'),
            include_label=True, source=SearchField
        )

        menu_facet.bind_links(
            links=(link_search, link_search_advanced),
            sources=(
                'search:search_simple', 'search:search_advanced',
                'search:search_results'
            )
        )
        menu_object.bind_links(
            links=(link_saved_resultset_delete_single,),
            sources=(SavedResultset,)
        )
        menu_list_facet.bind_links(
            links=(link_search_model_detail,),
            sources=(SearchModel,)
        )
        menu_list_facet.bind_links(
            links=(link_saved_resultset_result_list,),
            sources=(SavedResultset,)
        )
        menu_secondary.bind_links(
            links=(link_search_again,), sources=('search:search_results',)
        )
        menu_return.bind_links(
            links=(link_saved_resultset_list,), sources=(SavedResultset,)
        )
        menu_return.bind_links(
            links=(link_search_model_list,), sources=(
                SearchField, SearchModel
            )
        )
        menu_tools.bind_links(
            links=(
                link_saved_resultset_list, link_search_backend_reindex,
                link_search_model_list,
            )
        )
