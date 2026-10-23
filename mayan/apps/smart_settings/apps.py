from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.app_manager.classes import InitializationStep
from mayan.apps.app_manager.literals import PROCESS_INITIAL_SETUP
from mayan.apps.app_manager.runlevels import runlevel_core
from mayan.apps.common.menus import (
    menu_list_facet, menu_object, menu_return, menu_secondary, menu_setup
)
from mayan.apps.forms import column_widgets
from mayan.apps.navigation.source_columns import SourceColumn
from mayan.apps.views.template_cache_sources import (
    TemplateCacheSourceRegistry
)

from .classes import Setting
from .column_widgets import WidgetSettingValue
from .initializers import initializer_settings_save
from .links import (
    link_setting_cluster_configuration_save,
    link_setting_cluster_namespace_list, link_setting_edit,
    link_setting_namespace_detail, link_setting_namespace_list,
    link_setting_revert
)
from .namespaces import SettingNamespace
from .clusters import SettingCluster
from .setting_clusters import setting_cluster
from .widgets import setting_widget


class SmartSettingsApp(MayanAppConfig):
    app_namespace = 'settings'
    app_url = 'settings'
    has_static_media = True
    has_tests = True
    name = 'mayan.apps.smart_settings'
    verbose_name = _(message='Smart settings')

    def ready(self):
        super().ready()

        SettingCluster.load_modules()

        UpdatedStoredSetting = self.get_model(
            model_name='UpdatedStoredSetting'
        )

        TemplateCacheSourceRegistry.register_model(model=UpdatedStoredSetting)

        InitializationStep(
            function=initializer_settings_save,
            label=_(message='Save the settings configuration'),
            name='smart_settings.save', order=10,
            process=PROCESS_INITIAL_SETUP, runlevel=runlevel_core
        )

        SourceColumn(
            func=lambda context: len(
                context['object'].setting_dict
            ), label=_(message='Setting count'), include_label=True,
            source=SettingNamespace
        )
        SourceColumn(
            func=lambda context: setting_widget(
                context['object']
            ), label=_(message='Name'), is_identifier=True, source=Setting
        )
        SourceColumn(
            attribute='get_display_value', include_label=True,
            label=_(message='Value'), widget=WidgetSettingValue,
            source=Setting
        )
        SourceColumn(
            attribute='get_is_overridden', include_label=True, source=Setting,
            widget=column_widgets.TwoStateWidget
        )
        SourceColumn(
            attribute='get_has_value_new', include_label=True,
            source=Setting, widget=column_widgets.TwoStateWidget
        )
        SourceColumn(
            attribute='get_has_load_error', include_label=True,
            source=Setting, widget=column_widgets.TwoStateWidget
        )

        menu_list_facet.bind_links(
            links=(link_setting_namespace_detail,),
            sources=(SettingNamespace,)
        )
        menu_object.bind_links(
            links=(
                link_setting_edit, link_setting_revert
            ), sources=(Setting,)
        )
        menu_return.bind_links(
            links=(link_setting_namespace_list,), sources=(
                SettingNamespace, 'settings:setting_cluster_namespace_list'
            )
        )
        menu_secondary.bind_links(
            links=(link_setting_cluster_configuration_save,), sources=(
                SettingNamespace, Setting,
                'settings:setting_cluster_namespace_list'
            )
        )
        menu_setup.bind_links(
            links=(link_setting_cluster_namespace_list,)
        )

        setting_cluster.do_ready()
