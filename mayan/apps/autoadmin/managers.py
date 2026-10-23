import logging

from django.contrib.auth import get_user_model
from django.core import management
from django.db import models

from mayan.apps.authentication.secrets import get_random_password

from .literals import COMMAND_NAME_CREATESUPERUSER
from .settings import (
    setting_email, setting_log_credentials, setting_password, setting_username
)

logger = logging.getLogger(name=__name__)


class AutoAdminSingletonManager(models.Manager):
    def create_autoadmin(self):
        UserModel = get_user_model()

        if setting_password.value is None:
            password = get_random_password()
        else:
            password = setting_password.value

        try:
            UserModel.objects.get(
                **{UserModel.USERNAME_FIELD: setting_username.value}
            )
        except UserModel.DoesNotExist:
            if setting_log_credentials.value:
                logger.info(
                    'Creating super user -- login: %s, email: %s, password: %s',
                    setting_username.value, setting_email.value, password
                )

            management.call_command(
                COMMAND_NAME_CREATESUPERUSER,
                **{
                    UserModel.USERNAME_FIELD: setting_username.value,
                    'email': setting_email.value,
                    'interactive': False
                }
            )

            account = UserModel.objects.get(
                **{UserModel.USERNAME_FIELD: setting_username.value}
            )
            account.set_password(raw_password=password)
            account.save()
            auto_admin_properties, created = self.get_or_create()
            auto_admin_properties.account = account
            auto_admin_properties.password = password
            auto_admin_properties.password_hash = account.password
            auto_admin_properties.save()
        else:
            logger.error(
                'Super admin user already exists. -- login: %s',
                setting_username.value
            )
