from django.apps import apps
from django.core.exceptions import PermissionDenied
from django.utils.functional import cached_property

from .classes import Dashboard
from .literals import TEXT_DASHBOARD_UNKNOWN_NAME
from .permissions import permission_dashboard_view


class StoredDashboardBusinessLogicMixin:
    @cached_property
    def dashboard(self):
        return Dashboard.get(name=self.name)

    @property
    def label(self):
        try:
            dashboard = self.dashboard
        except KeyError:
            return TEXT_DASHBOARD_UNKNOWN_NAME % self.name
        else:
            return dashboard.label

    def get_widget_count(self):
        try:
            dashboard = self.dashboard
        except KeyError:
            return 0
        else:
            return dashboard.get_widget_count()

    def render(self, request):
        return self.dashboard.render(request=request)

    def render_for_user(self, request):
        AccessControlList = apps.get_model(
            app_label='acls', model_name='AccessControlList'
        )

        try:
            AccessControlList.objects.check_access(
                obj=self, permission=permission_dashboard_view,
                user=request.user
            )
        except PermissionDenied:
            return ''
        else:
            return self.render(request=request)
