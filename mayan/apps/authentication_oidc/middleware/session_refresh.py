import re

from django.conf import settings

from mozilla_django_oidc.middleware import SessionRefresh

from ..literals import SETTING_NAME_SESSION_REFRESH_EXEMPT_URLS


class SessionRefreshMayan(SessionRefresh):
    def __init__(self, get_response):
        super().__init__(get_response=get_response)

        pattern_list = getattr(
            settings, SETTING_NAME_SESSION_REFRESH_EXEMPT_URLS, ()
        )

        self.exempt_url_pattern_list = tuple(
            re.compile(pattern=pattern) for pattern in pattern_list
        )

    def get_is_exempt(self, request):
        for pattern in self.exempt_url_pattern_list:
            if pattern.match(request.path_info):
                return True

        return False

    def process_request(self, request):
        return None

    def process_view(self, request, view_func, view_args, view_kwargs):
        if self.get_is_exempt(request=request):
            return None

        return super().process_request(request=request)
