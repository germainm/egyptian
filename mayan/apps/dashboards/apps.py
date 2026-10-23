from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.classes import ModelPermission
from mayan.apps.acls.permissions import (
    permission_acl_edit, permission_acl_view
)
from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.common.menus import menu_object, menu_return, menu_tools
from mayan.apps.navigation.source_columns import SourceColumn

from .classes import Dashboard
from .handlers import handler_dashboard_initialize
from .links import link_dashboard_detail, link_dashboard_list
from .permissions import permission_dashboard_view


class DashboardsApp(MayanAppConfig):
    app_namespace = 'dashboards'
    app_url = 'dashboards'
    has_rest_api = False
    has_static_media = True
    has_tests = True
    name = 'mayan.apps.dashboards'
    verbose_name = _(message='Dashboards')

    def ready(self):
        super().ready()

        StoredDashboard = self.get_model(model_name='StoredDashboard')

        Dashboard.load_modules()

        ModelPermission.register(
            model=StoredDashboard, permissions=(
                permission_acl_edit, permission_acl_view,
                permission_dashboard_view
            )
        )

        SourceColumn(
            attribute='get_widget_count', label=_(message='Widgets'),
            include_label=True, source=StoredDashboard
        )
        SourceColumn(
            attribute='label', is_identifier=True, label=_(message='Label'),
            source=StoredDashboard
        )

        menu_object.bind_links(
            links=(link_dashboard_detail,), sources=(StoredDashboard,)
        )
        menu_return.bind_links(
            links=(link_dashboard_list,), sources=(
                StoredDashboard, 'dashboards:dashboard_list',
            )
        )
        menu_tools.bind_links(
            links=(link_dashboard_list,)
        )

        post_migrate.connect(
            dispatch_uid='dashboards_handler_dashboard_initialize',
            receiver=handler_dashboard_initialize, sender=self
        )
