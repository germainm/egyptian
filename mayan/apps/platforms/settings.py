from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster
from mayan.literals import (
    GUNICORN_BIND_ADDRESS, GUNICORN_LIMIT_REQUEST_LINE, GUNICORN_MAX_REQUESTS,
    GUNICORN_REQUESTS_JITTER, GUNICORN_TIMEOUT, GUNICORN_WORKER_CLASS,
    GUNICORN_WORKERS
)

from .literals import (
    DEFAULT_SETTINGS_MODULE, DEFAULT_PLATFORMS_CLIENT_BACKEND_ARGUMENTS,
    DEFAULT_PLATFORMS_CLIENT_BACKEND_ENABLED
)


setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='Platform'), name='platform'
)

setting_client_backend_enabled = setting_namespace.do_setting_add(
    default=DEFAULT_PLATFORMS_CLIENT_BACKEND_ENABLED,
    global_name='PLATFORMS_CLIENT_BACKEND_ENABLED', help_text=_(
        message='List of client backends to launch after startup. Use full '
        'dotted path to the client backend classes.'
    )
)
setting_client_backend_arguments = setting_namespace.do_setting_add(
    default=DEFAULT_PLATFORMS_CLIENT_BACKEND_ARGUMENTS,
    global_name='PLATFORMS_CLIENT_BACKEND_ARGUMENTS', help_text=_(
        message='Arguments for the client backends. Use the client backend '
        'dotted path as the dictionary key for the arguments in dictionary '
        'format.'
    )
)


setting_namespace.do_setting_add(
    default=DEFAULT_SETTINGS_MODULE, global_name='MAYAN_SETTINGS_MODULE',
    help_text=_(
        message='Load an alternate settings file.'
    )
)


setting_namespace.do_setting_add(
    default=GUNICORN_BIND_ADDRESS, global_name='MAYAN_GUNICORN_BIND_ADDRESS',
    help_text=_(
        message='Address and port to which Gunicorn will bind. Defaults '
        'to `0.0.0.0:8000` which listens on all interfaces.'
    )
)
setting_namespace.do_setting_add(
    default=GUNICORN_LIMIT_REQUEST_LINE,
    global_name='MAYAN_GUNICORN_LIMIT_REQUEST_LINE', help_text=_(
        message='Allows setting Gunicorn\'s `limit_request_line` value.'
    )
)
setting_namespace.do_setting_add(
    default=GUNICORN_MAX_REQUESTS, global_name='MAYAN_GUNICORN_MAX_REQUESTS',
    help_text=_(
        message='Allows setting Gunicorn\'s `max_requests` value.'
    )
)
setting_namespace.do_setting_add(
    default=GUNICORN_REQUESTS_JITTER,
    global_name='MAYAN_GUNICORN_REQUESTS_JITTER', help_text=_(
        message='Allows setting Gunicorn\'s `max_requests_jitter` value.'
    )
)
setting_namespace.do_setting_add(
    default=GUNICORN_TIMEOUT, global_name='MAYAN_GUNICORN_TIMEOUT',
    help_text=_(
        message='Allows setting Gunicorn\'s `timeout` value. With an '
        'asynchronous worker class this is not a limit on the duration of a '
        'request, but the interval after which an unresponsive worker is '
        'killed. A worker performing an operation that never hands back '
        'control, such as copying a large file between filesystems or '
        'compressing or encrypting one, stops reporting that it is alive '
        'and is killed along with every connection it is serving, including '
        'those of other users. Raise this value above the duration of the '
        'longest such operation.'
    )
)
setting_namespace.do_setting_add(
    default=GUNICORN_WORKER_CLASS, global_name='MAYAN_GUNICORN_WORKER_CLASS',
    help_text=_(
        message='Allows setting Gunicorn\'s `worker_class` value. Use an '
        'asynchronous worker class. A synchronous worker serves a single '
        'connection at a time and each open browser tab holds an event '
        'stream connection open, so idle tabs consume the available workers '
        'and the installation stops answering requests.'
    )
)
setting_namespace.do_setting_add(
    default=GUNICORN_WORKERS, global_name='MAYAN_GUNICORN_WORKERS',
    help_text=_(
        message='Allows setting Gunicorn\'s `workers` value.'
    )
)
