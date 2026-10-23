from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.documents.models.document_models import Document
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import (
    EventManagerMethodAfter, EventManagerSave
)

from ..events import (
    event_document_metadata_added, event_document_metadata_edited,
    event_document_metadata_removed
)

from .metadata_instance_model_mixins import DocumentMetadataBusinessLogicMixin
from .metadata_type_models import MetadataType


class DocumentMetadata(
    DocumentMetadataBusinessLogicMixin, ExtraDataModelMixin, models.Model
):
    _ordering_fields = ('value',)

    document = models.ForeignKey(
        on_delete=models.CASCADE, related_name='metadata', to=Document,
        verbose_name=_(message='Document')
    )
    metadata_type = models.ForeignKey(
        on_delete=models.CASCADE, to=MetadataType, verbose_name=_(
            message='Type'
        )
    )
    value = models.TextField(
        blank=True, help_text=_(
            message='The actual value stored in the metadata type field for '
            'the document.'
        ), null=True, verbose_name=_(message='Value')
    )

    class Meta:
        ordering = ('metadata_type',)
        unique_together = ('document', 'metadata_type')
        verbose_name = _(message='Document metadata')
        verbose_name_plural = _(message='Document metadata')

    def __str__(self):
        return str(self.metadata_type)

    def clean_fields(self, *args, **kwargs):
        super().clean_fields(*args, **kwargs)

        self.value = self.metadata_type.validate_value(
            document_type=self.document.document_type, value=self.value
        )

    @method_event(
        action_object='metadata_type',
        event=event_document_metadata_removed,
        event_manager_class=EventManagerMethodAfter,
        target='document'
    )
    def delete(self, enforce_required=True, *args, **kwargs):
        is_required_for_document_type = enforce_required and self.document.document_type.metadata.filter(
            required=True
        ).filter(metadata_type=self.metadata_type).exists()

        if is_required_for_document_type:
            raise ValidationError(
                message=_(
                    message='Metadata type is required for this document '
                    'type.'
                )
            )

        return super().delete(*args, **kwargs)

    def natural_key(self):
        return self.document.natural_key() + self.metadata_type.natural_key()
    natural_key.dependencies = [
        'documents.Document', 'metadata.MetadataType'
    ]

    @method_event(
        created={
            'action_object': 'metadata_type',
            'event': event_document_metadata_added,
            'target': 'document'
        },
        edited={
            'action_object': 'metadata_type',
            'event': event_document_metadata_edited,
            'target': 'document'
        },
        event_manager_class=EventManagerSave
    )
    def save(self, *args, **kwargs):
        is_not_valid_for_document_type = not self.document.document_type.metadata.filter(
            metadata_type=self.metadata_type
        ).exists()

        if is_not_valid_for_document_type:
            raise ValidationError(
                message=_(
                    message='Metadata type is not valid for this document '
                    'type.'
                )
            )

        return super().save(*args, **kwargs)


class DocumentMetadataSearchResult(DocumentMetadata):
    class Meta:
        proxy = True
