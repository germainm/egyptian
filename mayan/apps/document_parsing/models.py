from django.db import models
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.models.document_file_page_models import (
    DocumentFilePage
)
from mayan.apps.documents.models.document_type_models import DocumentType

from .managers import (
    DocumentFilePageContentManager, DocumentTypeSettingsManager
)


class DocumentFilePageContent(models.Model):
    document_file_page = models.OneToOneField(
        on_delete=models.CASCADE, related_name='content', to=DocumentFilePage,
        verbose_name=_(message='Document file page')
    )
    content = models.TextField(
        blank=True, help_text=_(
            message='The actual text content as extracted by the document '
            'parsing backend.'
        ), verbose_name=_(message='Content')
    )

    objects = DocumentFilePageContentManager()

    class Meta:
        verbose_name = _(message='Document file page content')
        verbose_name_plural = _(message='Document file page contents')

    def __str__(self):
        return force_str(s=self.document_file_page)


class DocumentTypeSettings(models.Model):
    document_type = models.OneToOneField(
        on_delete=models.CASCADE, related_name='parsing_settings',
        to=DocumentType, unique=True, verbose_name=_(message='Document type')
    )
    auto_parsing = models.BooleanField(
        default=True, help_text=_(
            message='Automatically queue newly created documents for parsing.'
        ), verbose_name=_(message='Auto parsing')
    )

    objects = DocumentTypeSettingsManager()

    def natural_key(self):
        return self.document_type.natural_key()
    natural_key.dependencies = ['documents.DocumentType']

    class Meta:
        verbose_name = _(message='Document type settings')
        verbose_name_plural = _(message='Document types settings')
