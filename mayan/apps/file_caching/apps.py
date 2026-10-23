from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.classes import ModelPermission
from mayan.apps.acls.permissions import (
    permission_acl_edit, permission_acl_view
)
from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.common.menus import (
    menu_multi_item, menu_object, menu_return, menu_tools
)
from mayan.apps.dashboards.dashboards import dashboard_administrator
from mayan.apps.events.classes import EventModelRegistry, ModelEventType
from mayan.apps.navigation.source_columns import SourceColumn

from .dashboard_widgets import (
    DashboardWidgetFileCacheSizeAllocated, DashboardWidgetFileCacheSizeUsed
)
from .events import (
    event_cache_edited, event_cache_partition_purged, event_cache_purged
)
from .handlers import handler_cache_prune_on_maximum_size_decrease
from .links import (
    link_cache_list, link_cache_purge_multiple,
    link_cache_purge_single, link_cache_tool
)
from .permissions import permission_cache_purge, permission_cache_view


class FileCachingAppConfig(MayanAppConfig):
    app_namespace = 'file_caching'
    app_url = 'file_caching'
    has_tests = True
    name = 'mayan.apps.file_caching'
    verbose_name = _(message='File caching')

    def ready(self):
        super().ready()

        Cache = self.get_model(model_name='Cache')
        CachePartition = self.get_model(model_name='CachePartition')

        EventModelRegistry.register(model=Cache)
        EventModelRegistry.register(model=CachePartition)

        ModelEventType.register(
            event_types=(event_cache_edited, event_cache_purged,),
            model=Cache
        )
        ModelEventType.register(
            event_types=(event_cache_partition_purged,), model=CachePartition
        )

        ModelPermission.register(
            model=Cache, permissions=(
                permission_acl_edit, permission_acl_view,
                permission_cache_purge, permission_cache_view
            )
        )

        SourceColumn(
            attribute='label', is_identifier=True,
            is_object_absolute_url=True, source=Cache
        )
        SourceColumn(
            attribute='defined_storage_name', is_sortable=True, source=Cache
        )
        SourceColumn(
            attribute='get_maximum_size_display', include_label=True,
            is_sortable=True, sort_field='maximum_size', source=Cache
        )
        SourceColumn(
            attribute='get_total_size_display', include_label=True,
            source=Cache
        )
        SourceColumn(
            attribute='get_partition_count', include_label=True,
            source=Cache
        )
        SourceColumn(
            attribute='get_partition_file_count', include_label=True,
            source=Cache
        )

        dashboard_administrator.add_widget(
            widget=DashboardWidgetFileCacheSizeUsed, order=99
        )
        dashboard_administrator.add_widget(
            widget=DashboardWidgetFileCacheSizeAllocated, order=99
        )

        menu_object.bind_links(
            links=(link_cache_purge_single,),
            sources=(Cache,)
        )
        menu_multi_item.bind_links(
            links=(link_cache_purge_multiple,),
            sources=(Cache,)
        )
        menu_return.bind_links(
            links=(link_cache_list,), sources=(
                Cache, 'file_caching:cache_list'
            )
        )
        menu_tools.bind_links(
            links=(link_cache_tool,)
        )

        post_save.connect(
            dispatch_uid='cache_prune_on_maximum_size_decrease',
            receiver=handler_cache_prune_on_maximum_size_decrease,
            sender=Cache
        )
