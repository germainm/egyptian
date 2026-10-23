from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .literals import (
    DEFAULT_AUTHENTICATION_BACKEND, DEFAULT_AUTHENTICATION_BACKEND_ARGUMENTS,
    DEFAULT_AUTHENTICATION_DISABLE_PASSWORD_RESET,


    DEFAULT_AUTHENTICATION_LOCKOUT_COOLOFF_TIME, DEFAULT_AUTHENTICATION_LOCKOUT_ENABLED,
    DEFAULT_AUTHENTICATION_LOCKOUT_FAILURE_LIMIT, DEFAULT_AUTHENTICATION_LOCKOUT_PARAMETERS,
    DEFAULT_AUTHENTICATION_LOCKOUT_RESET_ON_SUCCESS

)
from .setting_callbacks import callback_lockout_update

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='Authentication'), name='authentication'
)

setting_disable_password_reset = setting_namespace.do_setting_add(
    default=DEFAULT_AUTHENTICATION_DISABLE_PASSWORD_RESET,
    global_name='AUTHENTICATION_DISABLE_PASSWORD_RESET', help_text=_(
        message='Remove the "Forgot your password?" link on the login form '
        'used to trigger the password reset.'
    )
)
setting_authentication_backend = setting_namespace.do_setting_add(
    default=DEFAULT_AUTHENTICATION_BACKEND,
    global_name='AUTHENTICATION_BACKEND',
    help_text=_(
        message='Dotted path to the backend used to process user '
        'authentication.'
    )
)
setting_authentication_backend_arguments = setting_namespace.do_setting_add(
    default=DEFAULT_AUTHENTICATION_BACKEND_ARGUMENTS,
    global_name='AUTHENTICATION_BACKEND_ARGUMENTS',
    help_text=_(message='Arguments for the AUTHENTICATION_BACKEND.')
)


setting_authentication_lockout_enabled = setting_namespace.do_setting_add(
    default=DEFAULT_AUTHENTICATION_LOCKOUT_ENABLED,
    global_name='AUTHENTICATION_LOCKOUT_ENABLED',
    help_text=_(
        message='Enable failed-login monitoring and account lockout. When '
        'disabled, no lockout is enforced.'
    ),
    post_edit_function=callback_lockout_update
)
setting_authentication_lockout_failure_limit = setting_namespace.do_setting_add(
    default=DEFAULT_AUTHENTICATION_LOCKOUT_FAILURE_LIMIT,
    global_name='AUTHENTICATION_LOCKOUT_FAILURE_LIMIT',
    help_text=_(
        message='Number of consecutive failed login attempts before the '
        'account is locked.'
    ),
    post_edit_function=callback_lockout_update
)
setting_authentication_lockout_lockout_parameters = setting_namespace.do_setting_add(
    default=DEFAULT_AUTHENTICATION_LOCKOUT_PARAMETERS,
    global_name='AUTHENTICATION_LOCKOUT_PARAMETERS',
    help_text=_(
        message='Parameters used to identify which entity to lock. A flat '
        'list such as ["username", "ip_address"] locks either the '
        'username or the IP address independently when its own failure '
        'count reaches the limit. A nested list such as [["username", '
        '"ip_address"]] locks only the combination, requiring both to '
        'match before a request is blocked.'
    ),
    post_edit_function=callback_lockout_update
)
setting_authentication_lockout_cooloff_time = setting_namespace.do_setting_add(
    default=DEFAULT_AUTHENTICATION_LOCKOUT_COOLOFF_TIME,
    global_name='AUTHENTICATION_LOCKOUT_COOLOFF_TIME',
    help_text=_(
        message='Number of hours a locked account remains locked before it '
        'is automatically unlocked. A value of None disables the automatic '
        'unlock, keeping accounts locked until an administrator resets them. '
        'A value of 0 disables the lockout entirely, causing accumulated '
        'failures to never lock an account.'
    ),
    post_edit_function=callback_lockout_update
)
setting_authentication_lockout_reset_on_success = setting_namespace.do_setting_add(
    default=DEFAULT_AUTHENTICATION_LOCKOUT_RESET_ON_SUCCESS,
    global_name='AUTHENTICATION_LOCKOUT_RESET_ON_SUCCESS',
    help_text=_(
        message='Reset the accumulated failed-login counter for an '
        'account each time it logs in successfully.'
    ),
    post_edit_function=callback_lockout_update
)
