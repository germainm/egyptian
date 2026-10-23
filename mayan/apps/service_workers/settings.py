from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .literals import (
    DEFAULT_SERVICE_WORKERS_CACHE_REFRESH_INTERVAL,
    DEFAULT_SERVICE_WORKERS_ENABLED, DEFAULT_SERVICE_WORKERS_RETRY_INTERVAL
)

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='Service workers'), name='service_workers',
    version='0001'
)

setting_enabled = setting_namespace.do_setting_add(
    choices=('false', 'true'), default=DEFAULT_SERVICE_WORKERS_ENABLED,
    global_name='SERVICE_WORKERS_ENABLED', help_text=_(
        message='Register a client-side service worker that intercepts '
        'browser navigations and displays a branded, translated fallback '
        'page when the reverse proxy returns a gateway error (HTTP 502, 503, '
        'or 504) or the server is unreachable. Disabling this setting causes '
        'the service worker to unregister itself from browsers on their next '
        'visit.'
    )
)

setting_retry_interval = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_SERVICE_WORKERS_RETRY_INTERVAL,
    global_name='SERVICE_WORKERS_RETRY_INTERVAL', help_text=_(
        message='Number of seconds the "Service temporarily unavailable" '
        'page and panel wait before retrying the failed navigation '
        'automatically. Set to zero to disable the automatic retry and only '
        'offer the manual retry button.'
    )
)

setting_cache_refresh_interval = setting_namespace.do_setting_add(
    data_type=int,
    default=DEFAULT_SERVICE_WORKERS_CACHE_REFRESH_INTERVAL,
    global_name='SERVICE_WORKERS_CACHE_REFRESH_INTERVAL', help_text=_(
        message='Minimum number of seconds between the service worker '
        'refreshing its cached copy of the fallback page and its stylesheets '
        'while the user browses. Larger values reduce background requests; '
        'smaller values reflect theme or language changes sooner.'
    )
)
