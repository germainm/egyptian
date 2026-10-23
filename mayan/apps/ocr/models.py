from django.db import models
from django.utils.translation import gettext_lazy as _

from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.documents.models.document_type_models import DocumentType
from mayan.apps.documents.models.document_version_page_models import (
    DocumentVersionPage
)
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import EventManagerSave

from .events import event_ocr_document_version_page_content_edited
from .managers import (
    DocumentVersionPageOCRContentManager, DocumentTypeSettingsManager
)


class DocumentTypeOCRSettings(ExtraDataModelMixin, models.Model):
    document_type = models.OneToOneField(
        on_delete=models.CASCADE, related_name='ocr_settings',
        to=DocumentType, unique=True, verbose_name=_(message='Document type')
    )
    auto_ocr = models.BooleanField(
        default=True, help_text=_(
            message='Automatically queue newly created documents for OCR.'
        ), verbose_name=_(message='Auto OCR')
    )

    objects = DocumentTypeSettingsManager()

    class Meta:
        verbose_name = _(message='Document type settings')
        verbose_name_plural = _(message='Document types settings')

    def natural_key(self):
        return self.document_type.natural_key()
    natural_key.dependencies = ['documents.DocumentType']


class DocumentVersionPageOCRContent(models.Model):
    document_version_page = models.OneToOneField(
        on_delete=models.CASCADE, related_name='ocr_content',
        to=DocumentVersionPage, verbose_name=_(
            message='Document version page'
        )
    )
    content = models.TextField(
        blank=True, help_text=_(
            message='The actual text content extracted by the OCR backend.'
        ), verbose_name=_(message='Content')
    )

    objects = DocumentVersionPageOCRContentManager()

    class Meta:
        verbose_name = _(message='Document version page OCR content')
        verbose_name_plural = _(message='Document version pages OCR contents')

    def __str__(self):
        return str(self.document_version_page)

    @method_event(
        event_manager_class=EventManagerSave,
        edited={
            'action_object': 'document_version_page.document_version.document',
            'event': event_ocr_document_version_page_content_edited,
            'target': 'document_version_page'
        }
    )
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)
