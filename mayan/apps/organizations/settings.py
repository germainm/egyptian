from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .literals import (
    DEFAULT_ORGANIZATIONS_INSTALLATION_URL,
    DEFAULT_ORGANIZATIONS_URL_BASE_PATH
)
from .setting_validators import (
    validation_function_check_installation_url_format,
    validation_function_check_path_format
)

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='Organizations'), name='organizations'
)

setting_organization_installation_url = setting_namespace.do_setting_add(
    default=DEFAULT_ORGANIZATIONS_INSTALLATION_URL,
    global_name='ORGANIZATIONS_INSTALLATION_URL',
    help_text=_(
        message='Fully qualified domain including scheme, and port number if '
        'using a custom one. Do not include the path. Use the '
        'ORGANIZATIONS_URL_BASE_PATH setting to specify the path. '
        'Example: https://www.example.com:8080'
    ),
    validation_function=validation_function_check_installation_url_format
)
setting_organization_url_base_path = setting_namespace.do_setting_add(
    default=DEFAULT_ORGANIZATIONS_URL_BASE_PATH,
    global_name='ORGANIZATIONS_URL_BASE_PATH',
    help_text=_(
        message='Base URL path to use for all views. Used when hosting using '
        'a path that is not the root path of the web server. The path value '
        'must not include a leading or trailing slash. '
        'Example: mayan-installations/home'
    ), validation_function=validation_function_check_path_format
)
