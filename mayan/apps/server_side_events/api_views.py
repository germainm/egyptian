import logging
import time

from django.http import StreamingHttpResponse

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .classes import ServerEventStreamBackend
from .renderers import EventStreamRenderer
from .settings import (
    setting_connection_maximum_duration, setting_keepalive_interval,
    setting_poll_interval
)
from .utils import get_server_supports_concurrency

logger = logging.getLogger(name=__name__)


class APIEventStreamView(APIView):
    """
    get: Open a Server-Sent Events stream and push the events stored for the
    requesting user by the configured backend.

    Requires an async capable worker (the bundled gunicorn `gevent` worker, or
    the threaded development server); it must not be served by synchronous
    gunicorn workers, which would be tied up for the life of each connection.
    """
    permission_classes = (IsAuthenticated,)
    renderer_classes = (EventStreamRenderer,)
    swagger_schema = None
    synchronous_server_warning_emitted = False

    def do_synchronous_server_check(self, request):
        """
        Report a server that cannot serve anything else while an event stream
        is open. The stream is still served, as refusing it would leave the
        interface without its updates, but the deployment is unusable until
        the worker class is changed and the cause is not otherwise visible.
        The warning is emitted once per process to keep it out of every
        stream.
        """
        if APIEventStreamView.synchronous_server_warning_emitted:
            return

        if get_server_supports_concurrency(environ=request.META):
            return

        APIEventStreamView.synchronous_server_warning_emitted = True

        logger.warning(
            'The server is not able to process other requests while an '
            'event stream is open. Every browser tab holds one stream open, '
            'so the available workers will be exhausted and the '
            'installation will stop responding. Serve Mayan with an '
            'asynchronous worker; the Gunicorn `gevent` worker class is the '
            'supported option and is selected with the '
            '`MAYAN_GUNICORN_WORKER_CLASS` environment variable.'
        )

    def get(self, request, *args, **kwargs):
        self.do_synchronous_server_check(request=request)

        backend = ServerEventStreamBackend.get_instance()
        user = request.user

        cursor = request.META.get('HTTP_LAST_EVENT_ID') or None

        keepalive_interval = setting_keepalive_interval.value
        maximum_duration = setting_connection_maximum_duration.value
        poll_interval = setting_poll_interval.value

        def event_stream():
            nonlocal cursor

            if cursor is None:
                cursor = backend.get_initial_cursor(user=user)

            yield 'retry: {}\n\n'.format(poll_interval * 1000)
            yield ': connected\n\n'

            start_time = time.monotonic()
            last_activity = start_time

            try:
                while (time.monotonic() - start_time) < maximum_duration:
                    events, cursor = backend.get_events(
                        cursor=cursor, user=user
                    )

                    for event in events:
                        yield event.render()
                        last_activity = time.monotonic()

                    if (time.monotonic() - last_activity) >= keepalive_interval:
                        yield ': keepalive\n\n'
                        last_activity = time.monotonic()

                    backend.on_idle()
                    time.sleep(poll_interval)
            finally:
                backend.on_idle()

        response = StreamingHttpResponse(
            content_type='text/event-stream',
            streaming_content=event_stream()
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'

        return response
