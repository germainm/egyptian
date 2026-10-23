import re

from django.conf import settings
from django.contrib.auth.middleware import (
    LoginRequiredMiddleware as DjangoLoginRequiredMiddleware
)
from django.urls import NoReverseMatch, reverse


class LoginRequiredMiddleware(DjangoLoginRequiredMiddleware):

    def __init__(self, get_response):
        super().__init__(get_response=get_response)

        exempt_url_patterns = tuple(
            getattr(settings, 'LOGIN_REQUIRED_EXEMPT_URLS', ())
        )

        exempt_url_names = getattr(
            settings, 'LOGIN_REQUIRED_EXEMPT_URL_NAMES', ()
        )
        for url_name in exempt_url_names:
            try:
                exempt_url_patterns += (
                    r'^{}$'.format(
                        re.escape(
                            reverse(viewname=url_name)
                        )
                    ),
                )
            except NoReverseMatch:
                """
                Skip URL names that cannot be resolved at startup rather
                than abort the process. Apps may not be fully loaded yet
                or the name may belong to a disabled feature.
                """

        self.exempt_url_patterns = tuple(
            re.compile(pattern=pattern) for pattern in exempt_url_patterns
        )

    def process_view(self, request, view_func, view_args, view_kwargs):
        for pattern in self.exempt_url_patterns:
            if pattern.match(request.path_info):
                return None

        return super().process_view(
            request=request, view_args=view_args, view_func=view_func,
            view_kwargs=view_kwargs
        )
