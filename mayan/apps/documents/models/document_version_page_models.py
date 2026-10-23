from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import (
    EventManagerMethodAfter, EventManagerSave
)

from ..events import (
    event_document_version_page_created, event_document_version_page_deleted,
    event_document_version_page_edited
)
from ..managers import ValidDocumentVersionPageManager

from .document_version_models import DocumentVersion
from .document_version_page_model_mixins import (
    DocumentVersionPageBusinessLogicMixin
)
from .model_mixins import PagedModelMixin

__all__ = ('DocumentVersionPage', 'DocumentVersionPageSearchResult')


class DocumentVersionPage(
    DocumentVersionPageBusinessLogicMixin, ExtraDataModelMixin,
    PagedModelMixin, models.Model
):
    _paged_model_parent_field = 'document_version'

    document_version = models.ForeignKey(
        on_delete=models.CASCADE, related_name='version_pages',
        to=DocumentVersion, verbose_name=_(message='Document version')
    )
    page_number = models.PositiveIntegerField(
        db_index=True, default=1, help_text=_(
            message='Unique integer number for the page. Pages are ordered '
            'by this number.'
        ), verbose_name=_(message='Page number')
    )
    content_type = models.ForeignKey(
        help_text=_(
            message='Content type for the source object of the page.'
        ), on_delete=models.CASCADE, to=ContentType
    )
    object_id = models.PositiveIntegerField(
        help_text=_(message='ID for the source object of the page.')
    )
    content_object = GenericForeignKey(
        ct_field='content_type', fk_field='object_id'
    )

    class Meta:
        ordering = ('page_number',)
        unique_together = ('document_version', 'page_number')
        verbose_name = _(message='Document version page')
        verbose_name_plural = _(message='Document version pages')

    objects = models.Manager()
    valid = ValidDocumentVersionPageManager()

    def __str__(self):
        return self.get_label()

    @method_event(
        event_manager_class=EventManagerMethodAfter,
        event=event_document_version_page_deleted,
        target='document_version'
    )
    def delete(self, *args, **kwargs):
        self.cache_partition_delete()
        super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            kwargs={'document_version_page_id': self.pk},
            viewname='documents:document_version_page_view'
        )

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'action_object': 'document_version',
            'event': event_document_version_page_created,
            'target': 'self'
        },
        edited={
            'action_object': 'document_version',
            'event': event_document_version_page_edited,
            'target': 'self'
        }
    )
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class DocumentVersionPageSearchResult(DocumentVersionPage):
    class Meta:
        proxy = True
        verbose_name = _(message='Document version page')
        verbose_name_plural = _(message='Document version pages')
