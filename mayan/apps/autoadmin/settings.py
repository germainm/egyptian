from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .literals import (
    DEFAULT_AUTOADMIN_LOG_CREDENTIALS, DEFAULT_EMAIL, DEFAULT_PASSWORD,
    DEFAULT_USERNAME
)

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='Auto administrator'), name='autoadmin'
)

setting_email = setting_namespace.do_setting_add(
    default=DEFAULT_EMAIL, global_name='AUTOADMIN_EMAIL', help_text=_(
        message='Sets the email of the automatically created super user '
        'account.'
    )
)
setting_log_credentials = setting_namespace.do_setting_add(
    default=DEFAULT_AUTOADMIN_LOG_CREDENTIALS,
    global_name='AUTOADMIN_LOG_CREDENTIALS', help_text=_(
        message='Enables logging of the randomly generated super user '
        'credentials to the Python logging system at the ``INFO`` level '
        'under the logger `mayan.apps.autoadmin.managers`. This is intended '
        'for automated deployments and CI/CD pipelines that need to read '
        'the initial credentials from the application log. Has no effect '
        'when a fixed password is set via `AUTOADMIN_PASSWORD`.'
    )
)
setting_password = setting_namespace.do_setting_add(
    default=DEFAULT_PASSWORD, global_name='AUTOADMIN_PASSWORD', help_text=_(
        message='The password of the automatically created super user '
        'account. If it is equal to None, the password is randomly '
        'generated.'
    )
)
setting_username = setting_namespace.do_setting_add(
    default=DEFAULT_USERNAME, global_name='AUTOADMIN_USERNAME', help_text=_(
        message='The username of the automatically created super user '
        'account.'
    )
)
