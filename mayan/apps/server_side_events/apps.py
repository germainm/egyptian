from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig

from .classes import ServerEventStreamBackend


class ServerSideEventsApp(MayanAppConfig):
    app_namespace = 'server_side_events'
    app_url = 'sse'
    has_app_translations = True
    has_rest_api = True
    has_static_media = True
    has_tests = True
    name = 'mayan.apps.server_side_events'
    verbose_name = _(message='Server side events')

    def ready(self):
        super().ready()

        ServerEventStreamBackend.load_modules()
