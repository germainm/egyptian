from django.apps import apps
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.literals import TIME_DELTA_UNIT_CHOICES
from mayan.apps.common.validators import YAMLValidator
from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import (
    EventManagerMethodAfter, EventManagerSave
)

from ..classes import BaseDocumentFilenameGenerator
from ..events import (
    event_document_type_created, event_document_type_edited,
    event_document_type_quick_label_created,
    event_document_type_quick_label_deleted,
    event_document_type_quick_label_edited
)
from ..literals import (
    DEFAULT_DELETE_PERIOD, DEFAULT_DELETE_TIME_UNIT,
    DEFAULT_DOCUMENT_STUB_EXPIRATION_INTERVAL
)
from ..managers import DocumentTypeManager

from .document_type_model_mixins import DocumentTypeBusinessLogicMixin

__all__ = ('DocumentType', 'DocumentTypeFilename')


class DocumentType(
    DocumentTypeBusinessLogicMixin, ExtraDataModelMixin, models.Model
):
    _ordering_fields = ('label',)

    label = models.CharField(
        help_text=_(message='A short text identifying the document type.'),
        max_length=196, unique=True, verbose_name=_(message='Label')
    )
    filename_generator_backend = models.CharField(
        default=BaseDocumentFilenameGenerator.get_default(), help_text=_(
            message='The class responsible for producing the actual filename '
            'used to store the uploaded documents.'
        ), max_length=224, verbose_name=_(message='Filename generator backend')
    )
    filename_generator_backend_arguments = models.TextField(
        blank=True, help_text=_(
            message='The arguments for the filename generator backend as a '
            'YAML dictionary.'
        ), validators=[
            YAMLValidator()
        ], verbose_name=_(
            message='Filename generator backend arguments'
        )
    )


    trash_time_period = models.PositiveIntegerField(
        blank=True, help_text=_(
            message='Amount of time after which documents of this type will '
            'be moved to the trash.'
        ), null=True, verbose_name=_(message='Trash time period')
    )
    trash_time_unit = models.CharField(
        blank=True, choices=TIME_DELTA_UNIT_CHOICES, null=True, max_length=12,
        verbose_name=_(message='Trash time unit')
    )
    delete_time_period = models.PositiveIntegerField(
        blank=True, default=DEFAULT_DELETE_PERIOD, help_text=_(
            message='Amount of time after which documents of this type in '
            'the trash will be deleted.'
        ), null=True, verbose_name=_(message='Delete time period')
    )
    delete_time_unit = models.CharField(
        blank=True, choices=TIME_DELTA_UNIT_CHOICES,
        default=DEFAULT_DELETE_TIME_UNIT, max_length=12, null=True,
        verbose_name=_(message='Delete time unit')
    )
    document_stub_pruning_enabled = models.BooleanField(
        default=True, help_text=_(
            message='Delete documents that do not contain any files after a '
            'configured expiration interval.'
        ), verbose_name=_(message='Document stub pruning')
    )
    document_stub_expiration_interval = models.PositiveBigIntegerField(
        default=DEFAULT_DOCUMENT_STUB_EXPIRATION_INTERVAL, help_text=_(
            message='Time (in seconds) after which a document stub will be '
            'considered invalid and deleted, if pruning is enabled. This '
            'an optimization setting and should only be changed for '
            'specific circumstances.'
        ), verbose_name=_(message='Document stub expiration interval')
    )

    objects = DocumentTypeManager()

    class Meta:
        ordering = ('label',)
        verbose_name = _(message='Document type')
        verbose_name_plural = _(message='Document types')

    def __str__(self):
        return self.label

    def delete(self, *args, **kwargs):
        Document = apps.get_model(
            app_label='documents', model_name='Document'
        )

        for document in Document.objects.filter(document_type=self):
            document.delete(to_trash=False)

        return super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            kwargs={'document_type_id': self.pk},
            viewname='documents:document_type_document_list'
        )

    def natural_key(self):
        return (self.label,)

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'event': event_document_type_created,
            'target': 'self'
        },
        edited={
            'event': event_document_type_edited,
            'target': 'self'
        }
    )
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class DocumentTypeFilename(ExtraDataModelMixin, models.Model):
    _ordering_fields = ('filename', 'enabled')

    document_type = models.ForeignKey(
        on_delete=models.CASCADE, related_name='filenames', to=DocumentType,
        verbose_name=_(message='Document type')
    )
    filename = models.CharField(
        db_index=True, max_length=128, verbose_name=_(message='Label')
    )
    enabled = models.BooleanField(
        default=True, verbose_name=_(message='Enabled')
    )

    class Meta:
        ordering = ('filename',)
        unique_together = ('document_type', 'filename')
        verbose_name = _(message='Quick label')
        verbose_name_plural = _(message='Quick labels')

    def __str__(self):
        return self.filename

    @method_event(
        event_manager_class=EventManagerMethodAfter,
        event=event_document_type_quick_label_deleted,
        target='document_type',
    )
    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'event': event_document_type_quick_label_created,
            'action_object': 'document_type',
            'target': 'self'
        },
        edited={
            'event': event_document_type_quick_label_edited,
            'action_object': 'document_type',
            'target': 'self'
        }
    )
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)
