from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .literals import (
    DEFAULT_SERVER_SIDE_EVENTS_BACKEND,
    DEFAULT_SERVER_SIDE_EVENTS_BACKEND_ARGUMENTS,
    DEFAULT_SERVER_SIDE_EVENTS_CONNECTION_MAXIMUM_DURATION,
    DEFAULT_SERVER_SIDE_EVENTS_EVENT_RETENTION,
    DEFAULT_SERVER_SIDE_EVENTS_KEEPALIVE_INTERVAL,
    DEFAULT_SERVER_SIDE_EVENTS_POLL_INTERVAL
)

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='Server side events'), name='server_side_events'
)

setting_backend = setting_namespace.do_setting_add(
    default=DEFAULT_SERVER_SIDE_EVENTS_BACKEND,
    global_name='SERVER_SIDE_EVENTS_BACKEND', help_text=_(
        message='Full path to the backend used to store and retrieve the '
        'events pushed to the browsers via the server side event stream.'
    )
)
setting_backend_arguments = setting_namespace.do_setting_add(
    default=DEFAULT_SERVER_SIDE_EVENTS_BACKEND_ARGUMENTS,
    global_name='SERVER_SIDE_EVENTS_BACKEND_ARGUMENTS', help_text=_(
        message='Arguments to pass to the server side events backend.'
    )
)
setting_connection_maximum_duration = setting_namespace.do_setting_add(
    default=DEFAULT_SERVER_SIDE_EVENTS_CONNECTION_MAXIMUM_DURATION,
    global_name='SERVER_SIDE_EVENTS_CONNECTION_MAXIMUM_DURATION',
    help_text=_(
        message='Maximum number of seconds a single event stream connection '
        'is held open before it is closed so the client reconnects.'
    )
)
setting_event_retention = setting_namespace.do_setting_add(
    default=DEFAULT_SERVER_SIDE_EVENTS_EVENT_RETENTION,
    global_name='SERVER_SIDE_EVENTS_EVENT_RETENTION', help_text=_(
        message='Number of seconds a stored event is kept before it is '
        'deleted by the periodic clean up task. Used only by backends that '
        'store events, like the database backend.'
    )
)
setting_keepalive_interval = setting_namespace.do_setting_add(
    default=DEFAULT_SERVER_SIDE_EVENTS_KEEPALIVE_INTERVAL,
    global_name='SERVER_SIDE_EVENTS_KEEPALIVE_INTERVAL', help_text=_(
        message='Number of seconds between keep alive messages sent to hold '
        'the event stream connection open through intermediary proxies.'
    )
)
setting_poll_interval = setting_namespace.do_setting_add(
    default=DEFAULT_SERVER_SIDE_EVENTS_POLL_INTERVAL,
    global_name='SERVER_SIDE_EVENTS_POLL_INTERVAL', help_text=_(
        message='Number of seconds the event stream waits between checks for '
        'new events. Used only by backends that do not support blocking '
        'reads.'
    )
)
