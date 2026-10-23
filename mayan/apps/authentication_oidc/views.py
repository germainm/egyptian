from urllib.parse import quote, urlencode

from django.conf import settings
from django.contrib import auth
from django.http import HttpResponse
from django.shortcuts import resolve_url
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from mozilla_django_oidc.views import (
    OIDCAuthenticationCallbackView, OIDCAuthenticationRequestView
)

from mayan.apps.authentication.exceptions import AuthenticationError

from .literals import (
    HEADER_NAME_LOCATION, SESSION_KEY_RENEWAL_NEXT, SESSION_KEY_STATES,
    SESSION_KEY_UPSTREAM_NEXT, STATE_KEY_NEXT
)
from .utils import store_authorization_destination

import json

class MayanOIDCAuthenticationCallbackView(OIDCAuthenticationCallbackView):
    def get(self, request):
        state = request.GET.get('state')
        state_dict = request.session.get(SESSION_KEY_STATES, {})
        state_data = state_dict.get(state, {})
        code = request.GET.get('code')

        self.next_url = state_data.get(STATE_KEY_NEXT)

        self.authentication_attempt = bool(code and state_data)

        request.session.pop(SESSION_KEY_RENEWAL_NEXT, None)
        request.session.pop(SESSION_KEY_UPSTREAM_NEXT, None)

        return super().get(request=request)

    @property
    def failure_url(self):
        return resolve_url(
            self.get_settings('LOGIN_REDIRECT_URL_FAILURE', settings.LOGIN_URL)
        )

    def login_failure(self):
        self.next_url = None

        user = getattr(self.request, 'user', None)

        if self.authentication_attempt and user and user.is_authenticated:
            auth.logout(self.request)

        return super().login_failure()

    @property
    def success_url(self):
        next_url = getattr(self, 'next_url', None)

        if next_url:
            is_allowed = url_has_allowed_host_and_scheme(
                allowed_hosts={
                    self.request.get_host()
                }, require_https=self.request.is_secure(), url=next_url
            )

            if is_allowed:
                return next_url

        return resolve_url(
            self.get_settings('LOGIN_REDIRECT_URL', '/')
        )


class MayanOIDCAuthenticationRequestView(OIDCAuthenticationRequestView):
    def get(self, request):
        response = super().get(request=request)

        is_stored = store_authorization_destination(
            authorization_url=response[HEADER_NAME_LOCATION],
            destination=request.session.get(SESSION_KEY_UPSTREAM_NEXT),
            request=request
        )

        if not is_stored:
            raise AuthenticationError(
                'Unable to record the authorization attempt in the session.'
            )

        return response


class MayanOIDCSSOLogoutView(View):
    """
    Intermediate same-origin view that performs a client-side navigation to
    the OIDC provider's end_session_endpoint.

    Mayan's AJAX framework (partial_navigation.js) blocks cross-origin
    redirects in setLocation(). A server-side 302 to Keycloak would be
    followed by jQuery's XHR, triggering a CORS preflight that Keycloak
    rejects. By returning a 200 HTML page containing window.location.replace(),
    we let jQuery inject the script via .html(), which then performs a full
    browser navigation — no XHR, no CORS issue.
    """
    def get(self, request):
        logout_endpoint = getattr(settings, 'OIDC_OP_LOGOUT_ENDPOINT', None)

        if logout_endpoint:
            # Keycloak (18+) requires id_token_hint when
            # post_logout_redirect_uri is present. Without it the IdP
            # returns 400. OIDC_STORE_ID_TOKEN must be True for the token
            # to be stored in the session during authentication.
            id_token = request.session.get('oidc_id_token')

            logout_redirect_uri = getattr(
                settings, 'OIDC_LOGOUT_REDIRECT_URI', '/'
            )
            if id_token:
                logout_params = {
                    'id_token_hint': id_token,
                    'post_logout_redirect_uri': logout_redirect_uri,
                }
            else:
                # No id_token stored — use client_id as fallback.
                # Keycloak 18+ accepts client_id in place of id_token_hint
                # for RP-initiated logout when post_logout_redirect_uri is
                # whitelisted in the client's "Post Logout Redirect URIs".
                client_id = getattr(settings, 'OIDC_RP_CLIENT_ID', None)
                logout_params = {
                    'post_logout_redirect_uri': logout_redirect_uri,
                }
                if client_id:
                    logout_params['client_id'] = client_id

            keycloak_logout_url = '{}?{}'.format(
                logout_endpoint,
                urlencode(logout_params, quote_via=quote)
            ) if logout_params else logout_endpoint
        else:
            keycloak_logout_url = getattr(settings, 'LOGIN_URL', '/accounts/login/')

        html = (
            '<!doctype html><html><head><meta charset="utf-8"></head><body>'
            '<script>window.location.replace({url});</script>'
            '</body></html>'
        ).format(url=json.dumps(keycloak_logout_url))

        return HttpResponse(content=html, content_type='text/html')
