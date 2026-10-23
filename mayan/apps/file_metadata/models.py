from django.db import models
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.utils import convert_to_internal_name
from mayan.apps.common.validators import YAMLValidator
from mayan.apps.documents.models.document_file_models import DocumentFile
from mayan.apps.documents.models.document_type_models import DocumentType

from .managers import (
    FileMetadataEntryManager,
    ModelManagerDocumentTypeDriverConfigurationValid,
    ModelManagerStoredDriverValid
)
from .model_mixins import (
    DocumentFileDriverEntryBusinessLogicMixin,
    DocumentTypeDriverConfigurationBusinessLogicMixin,
    FileMetadataEntryBusinessLogicMixin,
    StoredDriverBusinessLogicMixin
)


class DocumentFileDriverEntry(
    DocumentFileDriverEntryBusinessLogicMixin, models.Model
):
    driver = models.ForeignKey(
        on_delete=models.CASCADE, related_name='driver_entries',
        to='StoredDriver', verbose_name=_(message='Driver')
    )
    document_file = models.ForeignKey(
        on_delete=models.CASCADE, related_name='file_metadata_drivers',
        to=DocumentFile, verbose_name=_(message='Document file')
    )

    class Meta:
        ordering = ('document_file', 'driver')
        unique_together = ('driver', 'document_file')
        verbose_name = _(message='Document file driver entry')
        verbose_name_plural = _(message='Document file driver entries')

    def __str__(self):
        return str(self.driver)


class DocumentTypeDriverConfiguration(
    DocumentTypeDriverConfigurationBusinessLogicMixin, models.Model
):
    _ordering_fields = ('enabled',)

    arguments = models.TextField(
        blank=True, help_text=_(
            message='Enter the arguments for the drive for the specific '
            'document type as a YAML dictionary. ie: {"degrees": 180}'
        ), validators=[
            YAMLValidator()
        ], verbose_name=_(message='Arguments')
    )
    document_type = models.ForeignKey(
        on_delete=models.CASCADE,
        related_name='file_metadata_driver_configurations',
        to=DocumentType, verbose_name=_(message='Document type')
    )
    stored_driver = models.ForeignKey(
        on_delete=models.CASCADE,
        related_name='document_type_configurations',
        to='StoredDriver', verbose_name=_(message='Driver')
    )
    enabled = models.BooleanField(
        default=True, help_text=_(
            'Enable this driver to process document files of the selected '
            'document type.'
        ), verbose_name=_(message='Enabled')
    )

    objects = models.Manager()
    valid = ModelManagerDocumentTypeDriverConfigurationValid()

    def __str__(self):
        return str(self.stored_driver)

    class Meta:
        ordering = ('stored_driver',)
        unique_together = ('document_type', 'stored_driver')
        verbose_name = _(message='Document type driver settings')
        verbose_name_plural = _(message='Document type driver settings')


class FileMetadataEntry(FileMetadataEntryBusinessLogicMixin, models.Model):
    _ordering_fields = ('internal_name', 'key', 'value')

    document_file_driver_entry = models.ForeignKey(
        on_delete=models.CASCADE, related_name='entries',
        to=DocumentFileDriverEntry,
        verbose_name=_(message='Document file driver entry')
    )
    internal_name = models.CharField(
        db_index=True, help_text=_(
            message='Normalized name of the file metadata entry.'
        ), max_length=255, verbose_name=_(message='Internal name')
    )
    key = models.CharField(
        help_text=_(
            message='Name of the file metadata entry as provided by the '
            'driver.'
        ), max_length=255, verbose_name=_(message='Key')
    )
    value = models.TextField(
        blank=True, help_text=_(message='Value of the file metadata entry.'),
        verbose_name=_(message='Value')
    )

    class Meta:
        ordering = ('internal_name', 'key')
        unique_together = ('document_file_driver_entry', 'internal_name')
        verbose_name = _(message='File metadata entry')
        verbose_name_plural = _(message='File metadata entries')

    objects = FileMetadataEntryManager()

    def __str__(self):
        return '{}: {}: {}'.format(
            self.document_file_driver_entry, self.key, self.value
        )

    def save(self, *args, **kwargs):
        internal_name = convert_to_internal_name(value=self.key)

        queryset_siblings = self.document_file_driver_entry.entries.exclude(
            pk=self.pk
        )

        queryset_duplicated = queryset_siblings.filter(
            internal_name=internal_name
        )

        if queryset_duplicated.exists():
            internal_name = '{}_{}'.format(
                internal_name, queryset_duplicated.count()
            )

        self.internal_name = internal_name

        super().save(*args, **kwargs)


class StoredDriver(StoredDriverBusinessLogicMixin, models.Model):
    _ordering_fields = ('internal_name',)

    driver_path = models.CharField(
        max_length=255, unique=True, verbose_name=_(message='Driver path')
    )
    internal_name = models.CharField(
        db_index=True, max_length=128, unique=True,
        verbose_name=_(message='Internal name')
    )
    exists = models.BooleanField(
        default=True, help_text=_(
            'The class defined by this instance is valid and active.'
        ), verbose_name=_(message='Valid')
    )

    objects = models.Manager()
    valid = ModelManagerStoredDriverValid()

    class Meta:
        ordering = ('internal_name',)
        verbose_name = _(message='Driver')
        verbose_name_plural = _(message='Drivers')

    def __str__(self):
        return str(self.driver_label)
