from django.db import models
from django.utils.translation import gettext_lazy as _

from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.documents.models.document_type_models import DocumentType
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import (
    EventManagerMethodAfter, EventManagerSave
)

from ..events import event_metadata_type_relationship_updated
from ..managers import DocumentTypeMetadataTypeManager

from .metadata_type_models import MetadataType


class DocumentTypeMetadataType(ExtraDataModelMixin, models.Model):
    document_type = models.ForeignKey(
        on_delete=models.CASCADE, related_name='metadata', to=DocumentType,
        verbose_name=_(message='Document type')
    )
    metadata_type = models.ForeignKey(
        on_delete=models.CASCADE, related_name='document_types',
        to=MetadataType, verbose_name=_(message='Metadata type')
    )
    required = models.BooleanField(
        default=False, verbose_name=_(message='Required')
    )

    objects = DocumentTypeMetadataTypeManager()

    class Meta:
        ordering = ('metadata_type',)
        unique_together = ('document_type', 'metadata_type')
        verbose_name = _(message='Document type metadata type options')
        verbose_name_plural = _(
            message='Document type metadata types options'
        )

    def __str__(self):
        return str(self.metadata_type)

    @method_event(
        action_object='metadata_type',
        event=event_metadata_type_relationship_updated,
        event_manager_class=EventManagerMethodAfter,
        target='document_type'
    )
    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)

    @method_event(
        created={
            'action_object': 'metadata_type',
            'event': event_metadata_type_relationship_updated,
            'target': 'document_type'
        },
        edited={
            'action_object': 'metadata_type',
            'event': event_metadata_type_relationship_updated,
            'target': 'document_type'
        },
        event_manager_class=EventManagerSave
    )
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)
