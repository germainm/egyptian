from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ..managers import DocumentFilePageManager, ValidDocumentFilePageManager

from .document_file_models import DocumentFile
from .document_file_page_model_mixins import (
    DocumentFilePageBusinessLogicMixin
)
from .document_version_page_models import DocumentVersionPage
from .model_mixins import PagedModelMixin

__all__ = ('DocumentFilePage', 'DocumentFilePageSearchResult')


class DocumentFilePage(
    DocumentFilePageBusinessLogicMixin, PagedModelMixin, models.Model
):
    _paged_model_parent_field = 'document_file'

    document_file = models.ForeignKey(
        on_delete=models.CASCADE, related_name='file_pages', to=DocumentFile,
        verbose_name=_(message='Document file')
    )
    page_number = models.PositiveIntegerField(
        db_index=True, default=1, editable=False,
        verbose_name=_(message='Page number')
    )

    objects = DocumentFilePageManager()
    valid = ValidDocumentFilePageManager()

    class Meta:
        ordering = ('page_number',)
        verbose_name = _(message='Document file page')
        verbose_name_plural = _(message='Document file pages')

    def __str__(self):
        return self.get_label()

    def delete(self, *args, **kwargs):
        content_type = ContentType.objects.get_for_model(
            model=self
        )
        queryset_document_version_page = DocumentVersionPage.objects.filter(
            content_type=content_type, object_id=self.pk
        )

        self.cache_partition_delete()

        for document_version_page in queryset_document_version_page:
            document_version_page._event_actor = getattr(
                self, '_event_actor', None
            )
            document_version_page.delete()

        super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            kwargs={'document_file_page_id': self.pk},
            viewname='documents:document_file_page_view'
        )

    def natural_key(self):
        return (
            self.page_number, self.document_file.natural_key()
        )
    natural_key.dependencies = ['documents.DocumentFile']


class DocumentFilePageSearchResult(DocumentFilePage):
    class Meta:
        ordering = ('document_file__document', 'page_number')
        proxy = True
        verbose_name = _(message='Document file page')
        verbose_name_plural = _(message='Document file pages')
