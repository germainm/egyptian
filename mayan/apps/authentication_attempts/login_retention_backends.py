from django.apps import apps
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from mayan.apps.backends.classes import BaseBackend


class LoginAttemptRetentionBackend(BaseBackend):
    _loader_module_name = 'login_retention_backends'

    @staticmethod
    def get_model():
        return apps.get_model(
            app_label='authentication_attempts', model_name='LoginAttempt'
        )

    def _execute(self):
        raise NotImplementedError

    def execute(self):
        self._execute()


class LoginAttemptRetentionBackendLatest(LoginAttemptRetentionBackend):
    label = _(message='Keep the last N login attempts')

    def __init__(self, number):
        self.number = number

    def _execute(self):
        LoginAttempt = self.get_model()

        queryset_remain = LoginAttempt.objects.order_by(
            '-datetime'
        ).values_list('pk')[:self.number]

        queryset_delete = LoginAttempt.objects.exclude(
            pk__in=queryset_remain
        )
        queryset_delete.delete()


class LoginAttemptRetentionBackendLatestPerUser(LoginAttemptRetentionBackend):
    label = _(message='Keep the last N login attempts per username')

    def __init__(self, number):
        self.number = number

    def _execute(self):
        LoginAttempt = self.get_model()

        queryset_remain = LoginAttempt.objects.filter(
            pk__in=models.Subquery(
                LoginAttempt.objects.filter(
                    username=models.OuterRef('username')
                ).order_by('-datetime').values('pk')[:self.number]
            )
        )

        queryset_delete = LoginAttempt.objects.exclude(
            pk__in=queryset_remain.values_list('pk')
        )
        queryset_delete.delete()


class LoginAttemptRetentionBackendOlderThanDays(LoginAttemptRetentionBackend):
    label = _(message='Delete login attempts older than N days')

    def __init__(self, days):
        self.days = days

    def _execute(self):
        LoginAttempt = self.get_model()

        cutoff_datetime = timezone.now() - timezone.timedelta(days=self.days)

        queryset = LoginAttempt.objects.filter(datetime__lt=cutoff_datetime)
        queryset.delete()
