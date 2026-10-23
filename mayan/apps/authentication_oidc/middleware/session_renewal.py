from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import Resolver404, resolve
from django.utils.deprecation import MiddlewareMixin
from django.utils.http import url_has_allowed_host_and_scheme

from mayan.apps.views.literals import HEADER_NAME_PAGE_RELOAD
from mayan.apps.views.utils import get_request_referer

from ..literals import (
    HEADER_NAME_LOCATION, HEADER_NAME_REFRESH_URL, SCHEME_LIST_PROVIDER,
    STATUS_CODE_REDIRECT, STATUS_CODE_RENEWAL, URL_NAMESPACE_API
)
from ..utils import store_authorization_destination


class SessionRenewalRedirect(MiddlewareMixin):
    def get_is_api_request(self, request):
        resolver_match = request.resolver_match

        if not resolver_match:
            urlconf = getattr(request, 'urlconf', None)

            try:
                resolver_match = resolve(
                    path=request.path_info, urlconf=urlconf
                )
            except Resolver404:
                return True

        return URL_NAMESPACE_API in resolver_match.namespaces

    def get_is_renewal_response(self, response):
        renewal_url = self.get_renewal_url(response=response)

        if not renewal_url:
            return False

        endpoint = getattr(
            settings, 'OIDC_OP_AUTHORIZATION_ENDPOINT', None
        )

        if not endpoint:
            return False

        try:
            endpoint_parts = urlsplit(url=endpoint)
        except ValueError:
            return False

        if endpoint_parts.scheme not in SCHEME_LIST_PROVIDER:
            return False

        if not endpoint_parts.netloc:
            return False

        try:
            renewal_parts = urlsplit(url=renewal_url)
        except ValueError:
            return False

        if renewal_parts.fragment:
            return False

        endpoint_identity = (
            endpoint_parts.scheme, endpoint_parts.netloc, endpoint_parts.path
        )
        renewal_identity = (
            renewal_parts.scheme, renewal_parts.netloc, renewal_parts.path
        )

        return renewal_identity == endpoint_identity

    def get_location(self, request):
        if self.get_is_api_request(request=request):
            location = get_request_referer(request=request)
        else:
            location = request.get_full_path()

        if not location:
            return None

        is_allowed = url_has_allowed_host_and_scheme(
            allowed_hosts={
                request.get_host()
            }, require_https=request.is_secure(), url=location
        )

        if is_allowed:
            return location

        return None

    def get_renewal_url(self, response):
        if response.status_code == STATUS_CODE_RENEWAL:
            return response.headers.get(HEADER_NAME_REFRESH_URL)

        if response.status_code == STATUS_CODE_REDIRECT:
            return response.headers.get(HEADER_NAME_LOCATION)

        return None

    def process_response(self, request, response):
        if not self.get_is_renewal_response(response=response):
            return response

        location = self.get_location(request=request)
        renewal_url = self.get_renewal_url(response=response)

        is_stored = store_authorization_destination(
            authorization_url=renewal_url, destination=location,
            request=request
        )

        if not is_stored:
            return response

        if response.status_code == STATUS_CODE_REDIRECT:
            return response

        response_renewal = HttpResponseRedirect(
            redirect_to=renewal_url
        )
        response_renewal[HEADER_NAME_PAGE_RELOAD] = 'true'

        return response_renewal
