from django.conf import settings
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.app_manager.classes import InitializationStep
from mayan.apps.app_manager.literals import PROCESS_INITIAL_SETUP
from mayan.apps.app_manager.runlevels import runlevel_core

from .handlers import handler_auto_admin_account_password_change
from .initializers import initializer_autoadmin_create


class AutoAdminAppConfig(MayanAppConfig):
    has_tests = True
    name = 'mayan.apps.autoadmin'
    verbose_name = _(message='Auto administrator')

    def ready(self):
        super().ready()

        InitializationStep(
            atomic=True, function=initializer_autoadmin_create,
            label=_(message='Create the administrator account'),
            name='autoadmin.create', process=PROCESS_INITIAL_SETUP,
            runlevel=runlevel_core
        )

        post_save.connect(
            dispatch_uid='autoadmin_handler_account_password_change',
            receiver=handler_auto_admin_account_password_change,
            sender=settings.AUTH_USER_MODEL
        )
