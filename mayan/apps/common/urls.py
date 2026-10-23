from django.urls import re_path

from .api_views import APIContentTypeDetailView, APIContentTypeListView
from .views import (
    AboutView, FaviconRedirectView, HomeView, LicenseView, ObjectCopyView,
    RootView, SetupListView, ToolsListView, TrademarkPolicyView
)

urlpatterns_misc = [
    re_path(
        route=r'^favicon\.ico$', view=FaviconRedirectView.as_view()
    ),
    re_path(
        route=r'^object/(?P<app_label>[-\w]+)/(?P<model_name>[-\w]+)/(?P<object_id>\d+)/copy/$',
        name='object_copy', view=ObjectCopyView.as_view()
    )
]

urlpatterns = [
    re_path(
        route=r'^$', name='root', view=RootView.as_view()
    ),
    re_path(
        route=r'^home/$', name='home', view=HomeView.as_view()
    ),
    re_path(
        route=r'^about/$', name='about_view', view=AboutView.as_view()
    ),
    re_path(
        route=r'^license/$', name='license_view', view=LicenseView.as_view()
    ),
    re_path(
        route=r'^trademark_policy/$', name='trademark_policy_view',
        view=TrademarkPolicyView.as_view()
    ),
    re_path(
        route=r'^setup/$', name='setup_list', view=SetupListView.as_view()
    ),
    re_path(
        route=r'^tools/$', name='tools_list', view=ToolsListView.as_view()
    )
]

urlpatterns.extend(urlpatterns_misc)

passthru_urlpatterns = []

api_urls = [
    re_path(
        route=r'^content_types/$', view=APIContentTypeListView.as_view(),
        name='content_type-list'
    ),
    re_path(
        route=r'^content_types/(?P<content_type_id>[0-9]+)/$',
        name='content_type-detail', view=APIContentTypeDetailView.as_view()
    )
]
