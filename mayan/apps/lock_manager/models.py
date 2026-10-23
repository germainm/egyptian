from django.db import models
from django.utils.translation import gettext_lazy as _

from .literals import DEFAULT_LOCK_MANAGER_DEFAULT_LOCK_TIMEOUT
from .managers import LockManager
from .model_mixins import LockBusinessLogicMixin
from .settings import setting_default_lock_timeout


class Lock(LockBusinessLogicMixin, models.Model):
    creation_datetime = models.DateTimeField(
        auto_now_add=True, verbose_name=_(message='Creation datetime')
    )
    timeout = models.IntegerField(
        default=DEFAULT_LOCK_MANAGER_DEFAULT_LOCK_TIMEOUT,
        verbose_name=_(message='Timeout')
    )
    name = models.CharField(
        max_length=255, unique=True, verbose_name=_(message='Name')
    )

    objects = LockManager()

    class Meta:
        verbose_name = _(message='Lock')
        verbose_name_plural = _(message='Locks')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.timeout:
            self.timeout = setting_default_lock_timeout.value

        super().save(*args, **kwargs)
