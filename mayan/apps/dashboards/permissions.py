from django.utils.translation import gettext_lazy as _

from mayan.apps.permissions.classes import PermissionNamespace

namespace = PermissionNamespace(
    label=_(message='Dashboards'), name='dashboards'
)

permission_dashboard_view = namespace.add_permission(
    label=_(message='View dashboards'), name='dashboard_view'
)
