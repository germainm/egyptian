import warnings

from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.common.menus import menu_list_facet, menu_return, menu_tools
from mayan.apps.navigation.source_columns import SourceColumn

from .classes import ModelProperty, ModelWrapper
from .literals import MESSAGE_SQLITE_WARNING
from .links import link_model_property_list, link_property_model_list
from .patches import patch_Migration
from .utils import check_for_sqlite
from .warnings import DatabaseWarning


class DatabasesApp(MayanAppConfig):
    app_namespace = 'databases'
    app_url = 'databases'
    has_tests = True
    name = 'mayan.apps.databases'
    verbose_name = _(message='Databases')

    def ready(self):
        super().ready()

        if check_for_sqlite():
            warnings.warn(
                category=DatabaseWarning,
                message=str(MESSAGE_SQLITE_WARNING)
            )

        patch_Migration()


        SourceColumn(
            attribute='get_label', include_label=True, is_identifier=True,
            source=ModelProperty
        )
        SourceColumn(
            attribute='get_description', include_label=True,
            source=ModelProperty
        )
        SourceColumn(
            attribute='get_name', include_label=True, source=ModelProperty
        )


        SourceColumn(
            attribute='get_name_full', include_label=True, is_identifier=True,
            source=ModelWrapper
        )
        SourceColumn(
            attribute='get_app_label', include_label=True,
            source=ModelWrapper
        )
        SourceColumn(
            attribute='get_label', include_label=True,
            source=ModelWrapper
        )


        menu_tools.bind_links(
            links=(link_property_model_list,)
        )

        menu_list_facet.bind_links(
            links=(link_model_property_list,), sources=(ModelWrapper,)
        )

        menu_return.bind_links(
            links=(link_property_model_list,), sources=(ModelWrapper,)
        )
