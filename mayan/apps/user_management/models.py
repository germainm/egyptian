from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import EventManagerSave

from .events import event_user_edited
from .managers import UserOptionsManager


class UserOptions(models.Model):
    user = models.OneToOneField(
        on_delete=models.CASCADE, related_name='user_options',
        to=settings.AUTH_USER_MODEL, unique=True, verbose_name=_(message='User')
    )
    block_password_change = models.BooleanField(
        default=False, verbose_name=_(
            message='Forbid this user from changing their password.'
        )
    )

    objects = UserOptionsManager()

    class Meta:
        verbose_name = _(message='User settings')
        verbose_name_plural = _(message='Users settings')

    def natural_key(self):
        return self.user.natural_key()
    natural_key.dependencies = [settings.AUTH_USER_MODEL]

    @method_event(
        event_manager_class=EventManagerSave,
        edited={
            'event': event_user_edited,
            'target': 'user'
        }
    )
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)
