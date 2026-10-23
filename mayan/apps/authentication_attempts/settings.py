from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .literals import (
    CONFIG_OPTION_LOG_FAILURE, CONFIG_OPTION_LOG_KNOWN_USERS_ONLY,
    CONFIG_OPTION_LOG_SUCCESS, DEFAULT_AUTHENTICATION_ATTEMPTS_CONFIG,
    DEFAULT_LOGIN_ATTEMPT_RETENTION_BACKEND,
    DEFAULT_LOGIN_ATTEMPT_RETENTION_BACKEND_ARGUMENTS,
    DEFAULT_LOGIN_ATTEMPT_RETENTION_TASK_INTERVAL
)

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='Authentication attempts'),
    name='authentication_attempts'
)

setting_authentication_attempts_config = setting_namespace.do_setting_add(
    default=DEFAULT_AUTHENTICATION_ATTEMPTS_CONFIG,
    global_name='AUTHENTICATION_ATTEMPTS_CONFIG',
    help_text=_(
        message='Dictionary of toggles that control which login attempts '
        'are recorded. `%(log_success)s` records successful logins. '
        '`%(log_failure)s` records failed logins. `%(log_known_users_only)s` '
        'records an attempt only when the supplied username matches an '
        'existing user. Enabling `%(log_known_users_only)s` reduces the '
        'chance of incidentally storing a secret typed into the username '
        'field, but it also stops the recording of attempts against '
        'non-existent accounts, which hides username enumeration and '
        'credential-stuffing activity. Leave it disabled unless the '
        'privacy trade-off is understood and accepted.'
    ) % {
        'log_failure': CONFIG_OPTION_LOG_FAILURE,
        'log_known_users_only': CONFIG_OPTION_LOG_KNOWN_USERS_ONLY,
        'log_success': CONFIG_OPTION_LOG_SUCCESS
    }
)
setting_login_attempt_retention_backend = setting_namespace.do_setting_add(
    default=DEFAULT_LOGIN_ATTEMPT_RETENTION_BACKEND,
    global_name='AUTHENTICATION_ATTEMPTS_RETENTION_BACKEND',
    help_text=_(
        message='Path to the login attempt retention subclass that will '
        'be called periodically to prune the login attempt log.'
    )
)
setting_login_attempt_retention_backend_arguments = setting_namespace.do_setting_add(
    default=DEFAULT_LOGIN_ATTEMPT_RETENTION_BACKEND_ARGUMENTS,
    global_name='AUTHENTICATION_ATTEMPTS_RETENTION_BACKEND_ARGUMENTS',
    help_text=_(
        message='Arguments to pass to '
        '`AUTHENTICATION_ATTEMPTS_RETENTION_BACKEND`.'
    )
)
setting_login_attempt_retention_task_interval = setting_namespace.do_setting_add(
    default=DEFAULT_LOGIN_ATTEMPT_RETENTION_TASK_INTERVAL,
    global_name='AUTHENTICATION_ATTEMPTS_RETENTION_TASK_INTERVAL',
    help_text=_(
        message='Time interval in seconds, at which the login attempt '
        'retention task will execute. When several retention backends are '
        'used, set this to the smallest interval any of them requires.'
    )
)


def get_authentication_attempts_setting_config_value(key):
    config = setting_authentication_attempts_config.value or {}

    return config.get(
        key, DEFAULT_AUTHENTICATION_ATTEMPTS_CONFIG[key]
    )
