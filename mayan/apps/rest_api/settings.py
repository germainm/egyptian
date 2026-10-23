from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .literals import (
    DEFAULT_REST_API_DISABLE_LINKS, DEFAULT_REST_API_MAXIMUM_PAGE_SIZE,
    DEFAULT_REST_API_PAGE_SIZE, DEFAULT_REST_API_THROTTLING_ENABLED,
    DEFAULT_REST_API_THROTTLING_RATE_ANONYMOUS,
    DEFAULT_REST_API_THROTTLING_RATE_USER
)
from .setting_validators import validation_function_check_throttling_rate

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='REST API'), name='rest_api', version='0001'
)

setting_disable_links = setting_namespace.do_setting_add(
    choices=('false', 'true'), default=DEFAULT_REST_API_DISABLE_LINKS,
    global_name='REST_API_DISABLE_LINKS', help_text=_(
        message='Disable the REST API links in the tools menu.'
    )
)
setting_maximum_page_size = setting_namespace.do_setting_add(
    default=DEFAULT_REST_API_MAXIMUM_PAGE_SIZE,
    global_name='REST_API_MAXIMUM_PAGE_SIZE', help_text=_(
        message='The maximum page size that can be requested.'
    )
)
setting_page_size = setting_namespace.do_setting_add(
    default=DEFAULT_REST_API_PAGE_SIZE,
    global_name='REST_API_PAGE_SIZE', help_text=_(
        message='The default page size if none is specified.'
    )
)
setting_throttling_enabled = setting_namespace.do_setting_add(
    choices=('false', 'true'),
    default=DEFAULT_REST_API_THROTTLING_ENABLED,
    global_name='REST_API_THROTTLING_ENABLED', help_text=_(
        message='Enable rate limiting of the REST API requests. When '
        'disabled, no throttling is enforced regardless of the configured '
        'rates.'
    )
)
setting_throttling_rate_anonymous = setting_namespace.do_setting_add(
    default=DEFAULT_REST_API_THROTTLING_RATE_ANONYMOUS,
    global_name='REST_API_THROTTLING_RATE_ANONYMOUS', help_text=_(
        message='Maximum number of REST API requests allowed for anonymous '
        'users, expressed as `<number>/<period>`. The period can be one of '
        '`second`, `minute`, `hour` or `day`. Example: 5/second. Leave '
        'blank to disable throttling of anonymous users.'
    ), validation_function=validation_function_check_throttling_rate
)
setting_throttling_rate_user = setting_namespace.do_setting_add(
    default=DEFAULT_REST_API_THROTTLING_RATE_USER,
    global_name='REST_API_THROTTLING_RATE_USER', help_text=_(
        message='Maximum number of REST API requests allowed for '
        'authenticated users, expressed as `<number>/<period>`. The period '
        'can be one of `second`, `minute`, `hour` or `day`. Example: '
        '10/second. Leave blank to disable throttling of authenticated '
        'users.'
    ), validation_function=validation_function_check_throttling_rate
)
