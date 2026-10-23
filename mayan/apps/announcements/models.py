from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import EventManagerSave

from .events import event_announcement_created, event_announcement_edited
from .managers import AnnouncementManager


class Announcement(ExtraDataModelMixin, models.Model):
    _ordering_fields = ('enabled', 'end_datetime', 'label', 'start_datetime')

    label = models.CharField(
        max_length=32, help_text=_(
            message='Short description of this announcement.'
        ), verbose_name=_(message='Label')
    )
    text = models.TextField(
        help_text=_(message='The actual text to be displayed.'),
        verbose_name=_(message='Text')
    )
    enabled = models.BooleanField(
        default=True, verbose_name=_(message='Enabled')
    )
    start_datetime = models.DateTimeField(
        blank=True, help_text=_(
            message='Date and time after which this announcement will be '
            'displayed.'
        ), null=True, verbose_name=_(message='Start date time')
    )
    end_datetime = models.DateTimeField(
        blank=True, help_text=_(
            message='Date and time until when this announcement is to be '
            'displayed.'
        ), null=True, verbose_name=_(message='End date time')
    )

    objects = AnnouncementManager()

    class Meta:
        ordering = ('label',)
        verbose_name = _(message='Announcement')
        verbose_name_plural = _(message='Announcements')

    def __str__(self):
        return self.label

    def get_absolute_url(self):
        return reverse(viewname='announcements:announcement_list')

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'event': event_announcement_created,
            'target': 'self'
        },
        edited={
            'event': event_announcement_edited,
            'target': 'self'
        }
    )
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)
