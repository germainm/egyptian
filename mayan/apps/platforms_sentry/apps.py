from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig


class PlatformsSentryApp(MayanAppConfig):
    app_namespace = 'platforms_sentry'
    app_url = 'platforms_sentry'
    has_rest_api = False
    has_tests = True
    name = 'mayan.apps.platforms_sentry'
    verbose_name = _(message='Platforms Sentry')
