from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import EventManagerSave

from .events import event_user_setting_edited
from .managers import UserSettingManager


class UserSetting(models.Model):
    user = models.ForeignKey(
        on_delete=models.CASCADE, related_name='appearance_settings',
        to=settings.AUTH_USER_MODEL, verbose_name=_(message='User')
    )
    namespace = models.CharField(
        db_index=True, help_text=_(
            message='Axis or frontend that owns this setting.'
        ), max_length=64, verbose_name=_(message='Namespace')
    )
    key = models.CharField(
        db_index=True, max_length=64, verbose_name=_(message='Key')
    )
    value = models.TextField(
        blank=True, verbose_name=_(message='Value')
    )

    objects = UserSettingManager()

    class Meta:
        ordering = ('namespace', 'key')
        unique_together = ('user', 'namespace', 'key')
        verbose_name = _(message='User setting')
        verbose_name_plural = _(message='User settings')

    def __str__(self):
        return '{}.{}={}'.format(self.namespace, self.key, self.value)

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'event': event_user_setting_edited,
            'target': 'user'
        },
        edited={
            'event': event_user_setting_edited,
            'target': 'user'
        }
    )
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)
