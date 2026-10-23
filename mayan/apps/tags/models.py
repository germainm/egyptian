from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.documents.models.document_models import Document
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import EventManagerSave

from .events import event_tag_created, event_tag_edited
from .model_mixins import TagBusinessLogicMixin


class Tag(ExtraDataModelMixin, TagBusinessLogicMixin, models.Model):
    _ordering_fields = ('id', 'label')

    label = models.CharField(
        db_index=True, help_text=_(
            message='A short text used as the tag name.'
        ), max_length=128, unique=True, verbose_name=_(message='Label')
    )
    color = models.CharField(
        help_text=_(message='The RGB color values for the tag.'),
        max_length=7, verbose_name=_(message='Color')
    )
    documents = models.ManyToManyField(
        related_name='tags', to=Document, verbose_name=_(message='Documents')
    )

    class Meta:
        ordering = ('label',)
        verbose_name = _(message='Tag')
        verbose_name_plural = _(message='Tags')

    def __str__(self):
        return self.label

    def get_absolute_url(self):
        return reverse(
            kwargs={'tag_id': self.pk}, viewname='tags:tag_document_list'
        )

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'event': event_tag_created,
            'target': 'self'
        },
        edited={
            'event': event_tag_edited,
            'target': 'self'
        }
    )
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class DocumentTag(Tag):
    class Meta:
        proxy = True
        verbose_name = _(message='Document tag')
        verbose_name_plural = _(message='Document tags')
