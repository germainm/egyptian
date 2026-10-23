from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.backends.model_mixins import BackendModelMixin
from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import EventManagerSave

from .classes import MailerBackendNull
from .events import (
    event_mailing_profile_created, event_mailing_profile_edited
)
from .managers import UserMailerManager
from .model_mixins import UserMailerBusinessLogicMixin


class UserMailer(
    BackendModelMixin, ExtraDataModelMixin, UserMailerBusinessLogicMixin,
    models.Model
):
    _backend_model_null_backend = MailerBackendNull
    _ordering_fields = ('default', 'enabled', 'label')

    label = models.CharField(
        help_text=_(message='A short text describing the mailing profile.'),
        max_length=128, unique=True, verbose_name=_(message='Label')
    )
    default = models.BooleanField(
        default=True, help_text=_(
            message='If default, this mailing profile will be '
            'pre-selected on the document mailing form.'
        ), verbose_name=_(message='Default')
    )
    enabled = models.BooleanField(
        default=True, verbose_name=_(message='Enabled')
    )

    objects = UserMailerManager()

    class Meta:
        ordering = ('label',)
        verbose_name = _(message='Mailing profile')
        verbose_name_plural = _(message='Mailing profiles')

    def __str__(self):
        return self.label

    def get_absolute_url(self):
        return reverse(viewname='mailer:mailing_profile_list')

    def natural_key(self):
        return (self.label,)

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'event': event_mailing_profile_created,
            'target': 'self'
        },
        edited={
            'event': event_mailing_profile_edited,
            'target': 'self'
        }
    )
    def save(self, *args, **kwargs):
        if self.default:
            UserMailer.objects.select_for_update().exclude(
                pk=self.pk
            ).update(default=False)

        return super().save(*args, **kwargs)
