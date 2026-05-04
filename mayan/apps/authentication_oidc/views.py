from urllib.parse import quote, urlencode

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import resolve_url
from django.views import View

from mozilla_django_oidc.views import OIDCAuthenticationCallbackView

import json

class MayanOIDCAuthenticationCallbackView(OIDCAuthenticationCallbackView):
    @property
    def success_url(self):
        # Pull the next url from the session or settings--we don't need to
        # sanitize here because it should already have been sanitized.
        next_url = self.request.session.get('oidc_login_next', None)
        return next_url or resolve_url(
            self.get_settings('LOGIN_REDIRECT_URL', '/')
        )


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
