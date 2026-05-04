from django.urls import include, path, re_path

from .views import (
    MayanOIDCAuthenticationCallbackView, MayanOIDCSSOLogoutView
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
    # Directly override oidc/callback as ``OIDC_CALLBACK_CLASS`` is read
    # before the app loads therefore setting it in the .ready() method has
    # no effect.
    path(
        'oidc/callback/', MayanOIDCAuthenticationCallbackView.as_view(),
        name='oidc_authentication_callback'
    )
]
