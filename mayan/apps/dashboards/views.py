from django.utils.translation import gettext_lazy as _

from mayan.apps.views.generics import SimpleView, SingleObjectListView
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from .icons import icon_dashboard_detail, icon_dashboard_list
from .models import StoredDashboard
from .permissions import permission_dashboard_view


class DashboardDetailView(ExternalObjectViewMixin, SimpleView):
    external_object_permission = permission_dashboard_view
    external_object_pk_url_kwarg = 'dashboard_id'
    external_object_queryset = StoredDashboard.objects.all()
    template_name = 'dashboards/dashboard_detail.html'
    view_icon = icon_dashboard_detail

    def get_extra_context(self):
        return {
            'object': self.external_object,
            'title': _(message='Dashboard detail')
        }


class DashboardListView(SingleObjectListView):
    model = StoredDashboard
    object_permission = permission_dashboard_view
    view_icon = icon_dashboard_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_dashboard_list,
            'no_results_text': _(
                message='Dashboards group related widgets to show a quick '
                'summary of specific workflows or system activities.'
            ),
            'no_results_title': _(message='No dashboards available'),
            'title': _(message='Dashboards')
        }
