import requests

from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.authentication.classes import AuthenticationBackend
from mayan.apps.authentication.exceptions import AuthenticationError
from mayan.apps.common.classes import UpstreamSettingCollection
from mayan.apps.common.utils import get_class_full_name

from .django_authentication_backends import DjangoAuthenticationBackendOIDC
from .forms import AuthenticationFormOIDC
from .middleware.session_refresh import SessionRefreshMayan
from .middleware.session_renewal import SessionRenewalRedirect
from .setting_validators import validation_function_check_renewal_interval
from .literals import (
    DEFAULT_HTTP_TIMEOUT, DEFAULT_OIDC_OP_AUTHORIZATION_ENDPOINT,
    DEFAULT_OIDC_LOGOUT_REDIRECT_URI, DEFAULT_OIDC_OP_JWKS_ENDPOINT,
    DEFAULT_OIDC_OP_LOGOUT_ENDPOINT, DEFAULT_OIDC_OP_TOKEN_ENDPOINT,
    DEFAULT_OIDC_OP_USER_ENDPOINT,
    DEFAULT_OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS, DEFAULT_OIDC_RP_CLIENT_ID,
    DEFAULT_OIDC_RP_CLIENT_SECRET, DEFAULT_OIDC_RP_SIGN_ALGO,
    DEFAULT_OIDC_STORE_ID_TOKEN, DEFAULT_OIDC_USERNAME_ALGO,
    PATH_AUTHENTICATION_CLASS_OIDC
)

MIDDLEWARE_SESSION_REFRESH = get_class_full_name(klass=SessionRefreshMayan)
MIDDLEWARE_SESSION_RENEWAL_REDIRECT = get_class_full_name(
    klass=SessionRenewalRedirect
)

MIDDLEWARE_LIST = (
    MIDDLEWARE_SESSION_RENEWAL_REDIRECT, MIDDLEWARE_SESSION_REFRESH
)


class AuthenticationBackendOIDC(AuthenticationBackend):
    # ModelBackend lets local accounts log in when the OIDC provider is
    # unavailable.
    django_authentication_backend_paths = (
        get_class_full_name(klass=DjangoAuthenticationBackendOIDC),
        get_class_full_name(klass=ModelBackend),
    )
    login_form_class = AuthenticationFormOIDC

    def __init__(
        self, oidc_discovery_timeout=None, oidc_discovery_url=None, **kwargs
    ):
        if oidc_discovery_url:
            timeout = oidc_discovery_timeout or DEFAULT_HTTP_TIMEOUT
            response = requests.get(timeout=timeout, url=oidc_discovery_url)
            response.raise_for_status()
            data = response.json()

            try:
                kwargs['oidc_op_authorization_endpoint'] = data['authorization_endpoint']
                kwargs['oidc_op_jwks_endpoint'] = data['jwks_uri']
                kwargs['oidc_op_token_endpoint'] = data['token_endpoint']
                kwargs['oidc_op_user_endpoint'] = data['userinfo_endpoint']
            except KeyError:
                raise AuthenticationError(
                    'Unable to extract OIDC provider discovery information.'
                )

            # end_session_endpoint is optional in the OIDC spec.
            if 'end_session_endpoint' in data:
                kwargs.setdefault(
                    'oidc_op_logout_endpoint', data['end_session_endpoint']
                )

        upstream_setting_collection = UpstreamSettingCollection(
            name='mozilla_django_oidc'
        )
        upstream_setting_collection.do_setting_add(
            default=DEFAULT_OIDC_OP_AUTHORIZATION_ENDPOINT,
            name='OIDC_OP_AUTHORIZATION_ENDPOINT'
        )
        upstream_setting_collection.do_setting_add(
            default=DEFAULT_OIDC_OP_JWKS_ENDPOINT,
            name='OIDC_OP_JWKS_ENDPOINT'
        )
        upstream_setting_collection.do_setting_add(
            default=DEFAULT_OIDC_OP_TOKEN_ENDPOINT,
            name='OIDC_OP_TOKEN_ENDPOINT'
        )
        upstream_setting_collection.do_setting_add(
            default=DEFAULT_OIDC_OP_USER_ENDPOINT,
            name='OIDC_OP_USER_ENDPOINT'
        )
        upstream_setting_collection.do_setting_add(
            data_type=float,
            default=DEFAULT_OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS,
            name='OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS',
            validation_function=validation_function_check_renewal_interval
        )
        upstream_setting_collection.do_setting_add(
            default=DEFAULT_OIDC_RP_CLIENT_ID,
            name='OIDC_RP_CLIENT_ID'
        )
        upstream_setting_collection.do_setting_add(
            default=DEFAULT_OIDC_RP_CLIENT_SECRET,
            name='OIDC_RP_CLIENT_SECRET'
        )
        upstream_setting_collection.do_setting_add(
            default=DEFAULT_OIDC_RP_SIGN_ALGO,
            name='OIDC_RP_SIGN_ALGO'
        )
        upstream_setting_collection.do_setting_add(
            default=DEFAULT_OIDC_USERNAME_ALGO,
            name='OIDC_USERNAME_ALGO'
        )
        upstream_setting_collection.do_setting_add(
            default=DEFAULT_OIDC_OP_LOGOUT_ENDPOINT,
            name='OIDC_OP_LOGOUT_ENDPOINT'
        )
        upstream_setting_collection.do_setting_add(
            default=DEFAULT_OIDC_LOGOUT_REDIRECT_URI,
            name='OIDC_LOGOUT_REDIRECT_URI'
        )
        upstream_setting_collection.do_setting_add(
            default=DEFAULT_OIDC_STORE_ID_TOKEN,
            name='OIDC_STORE_ID_TOKEN'
        )

        upstream_setting_collection.do_kwargs_capture(**kwargs)

        super().__init__()

    def do_deinitialize(self):
        super().do_deinitialize()

        settings.MIDDLEWARE = tuple(
            [
                item for item in settings.MIDDLEWARE
                if item not in MIDDLEWARE_LIST
            ]
        )

        settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = tuple(
            [
                item for item in settings.REST_FRAMEWORK[
                    'DEFAULT_AUTHENTICATION_CLASSES'
                ] if item != PATH_AUTHENTICATION_CLASS_OIDC
            ]
        )

    def do_initialize(self):
        super().do_initialize()

        middleware_list = tuple(
            [
                item for item in settings.MIDDLEWARE
                if item not in MIDDLEWARE_LIST
            ]
        )

        settings.MIDDLEWARE = middleware_list + MIDDLEWARE_LIST

        authentication_class_list = tuple(
            [
                item for item in settings.REST_FRAMEWORK[
                    'DEFAULT_AUTHENTICATION_CLASSES'
                ] if item != PATH_AUTHENTICATION_CLASS_OIDC
            ]
        )

        settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
            PATH_AUTHENTICATION_CLASS_OIDC,
        ) + authentication_class_list

        # Redirect to the same-origin intermediate view which performs the
        # cross-origin navigation to Keycloak client-side, bypassing the
        # CORS restriction imposed by Mayan's AJAX framework on server-side
        # cross-origin redirects.
        if getattr(settings, 'OIDC_OP_LOGOUT_ENDPOINT', None):
            settings.LOGOUT_REDIRECT_URL = 'oidc_sso_logout'

    def get_context_data(self):
        return {
            'form_action': reverse(viewname='oidc_authentication_init'),
            'submit_button_css_extra_classes': 'center-block',
            'submit_label': _(message='Login via OIDC'),
            'submit_method': 'get'
        }
