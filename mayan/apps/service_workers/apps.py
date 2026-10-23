from django.conf import settings
from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig

from .literals import URL_PATTERN_LIST_SESSION_REFRESH_EXEMPT


class ServiceWorkersApp(MayanAppConfig):
    app_namespace = 'service_workers'
    app_url = ''
    has_static_media = True
    has_tests = True
    name = 'mayan.apps.service_workers'
    verbose_name = _(message='Service workers')

    def ready(self):
        super().ready()

        settings.SESSION_REFRESH_EXEMPT_URLS += (
            URL_PATTERN_LIST_SESSION_REFRESH_EXEMPT
        )
