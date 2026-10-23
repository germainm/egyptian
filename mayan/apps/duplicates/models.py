from django.db import models
from django.utils.translation import gettext_lazy as _

from mayan.apps.backends.model_mixins import BackendModelMixin
from mayan.apps.documents.models.document_models import Document

from .classes import NullBackend
from .managers import (
    DuplicateBackendEntryManager, StoredDuplicateBackendManager
)
from .model_mixins import (
    DuplicateBackendEntryBusinessLogicMixin,
    StoredDuplicateBackendBusinessLogicMixin
)


class StoredDuplicateBackend(
    BackendModelMixin, StoredDuplicateBackendBusinessLogicMixin, models.Model
):
    _backend_model_null_backend = NullBackend

    objects = StoredDuplicateBackendManager()

    class Meta:
        ordering = ('backend_path',)
        verbose_name = _(message='Stored duplicate backend')
        verbose_name_plural = _(message='Stored duplicate backends')

    def __str__(self):
        backend_class_label = self.get_backend_class_label()

        return str(backend_class_label)

    __str__.short_description = _(message='Label')


class DuplicateBackendEntry(
    DuplicateBackendEntryBusinessLogicMixin, models.Model
):
    stored_backend = models.ForeignKey(
        on_delete=models.CASCADE, related_name='duplicate_entries',
        to=StoredDuplicateBackend, verbose_name=_(
            message='Stored duplicate backend'
        )
    )
    document = models.ForeignKey(
        on_delete=models.CASCADE, related_name='duplicate_backend_entries',
        to=Document, verbose_name=_(message='Document')
    )
    documents = models.ManyToManyField(
        related_name='as_duplicate', to=Document, verbose_name=_(
            message='Duplicated documents'
        )
    )

    objects = DuplicateBackendEntryManager()

    class Meta:
        ordering = ('stored_backend__backend_path',)
        unique_together = ('stored_backend', 'document')
        verbose_name = _(message='Duplicated backend entry')
        verbose_name_plural = _(message='Duplicated backend entries')


class DuplicateSourceDocument(Document):
    class Meta:
        proxy = True


class DuplicateTargetDocument(Document):
    class Meta:
        proxy = True
