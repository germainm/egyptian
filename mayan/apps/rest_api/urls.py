from django.urls import include, re_path

from drf_spectacular.views import SpectacularRedocView, SpectacularSwaggerView
from rest_framework.urlpatterns import format_suffix_patterns

from .api_views import (
    APIRoot, APIVersionRoot, BatchRequestAPIView, BrowseableObtainAuthToken,
    ProjectInformationAPIView, SchemaAPIView
)
from .literals import API_VERSION

api_version_urls = [
    re_path(
        route=r'^$', name='api_version_root', view=APIVersionRoot.as_view()
    ),
    re_path(
        route=r'^auth/token/obtain/$', name='auth_token_obtain',
        view=BrowseableObtainAuthToken.as_view()
    ),
    re_path(
        route=r'^project/$', name='project_information',
        view=ProjectInformationAPIView.as_view()
    ),
    re_path(
        route=r'^batch_requests/$', name='batchrequest-create',
        view=BatchRequestAPIView.as_view()
    )
]

api_schema_urls = format_suffix_patterns(
    [
        re_path(
            route=r'^swagger$', name='schema-json',
            view=SchemaAPIView.as_view()
        )
    ], allowed=['json', 'yaml']
)

api_urls = [
    *api_schema_urls,
    re_path(
        route=r'^v{}/'.format(API_VERSION), view=include(api_version_urls)
    ),
    re_path(
        route=r'^$', name='api_root', view=APIRoot.as_view()
    )
]

urlpatterns = [
    re_path(
        route=r'^swagger/ui/$', name='schema-swagger-ui',
        view=SpectacularSwaggerView.as_view(url_name='rest_api:schema-json')
    ),
    re_path(
        route=r'^redoc/ui/$', name='schema-redoc',
        view=SpectacularRedocView.as_view(
            template_name='rest_api/redoc.html',
            url_name='rest_api:schema-json'
        )
    ),
    re_path(
        route=r'^', view=include(api_urls)
    )
]
