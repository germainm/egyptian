from django.urls import include, path, re_path

from .views import (
    MayanOIDCAuthenticationCallbackView, MayanOIDCAuthenticationRequestView,
    MayanOIDCSSOLogoutView
)

passthru_urlpatterns = [
    re_path(
        r'^oidc/', include('mozilla_django_oidc.urls')
    ),
    path(
        'oidc/sso-logout/', MayanOIDCSSOLogoutView.as_view(),
        name='oidc_sso_logout'
    ),
]

urlpatterns = [
    path(
        'oidc/authenticate/', MayanOIDCAuthenticationRequestView.as_view(),
        name='oidc_authentication_init'
    ),
    path(
        'oidc/callback/', MayanOIDCAuthenticationCallbackView.as_view(),
        name='oidc_authentication_callback'
    )
]
