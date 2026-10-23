from django.urls import re_path

from .views import DashboardDetailView, DashboardListView

urlpatterns = [
    re_path(
        route=r'^dashboards/$', name='dashboard_list',
        view=DashboardListView.as_view()
    ),
    re_path(
        route=r'^dashboards/(?P<dashboard_id>\d+)/$',
        name='dashboard_detail', view=DashboardDetailView.as_view()
    )
]
