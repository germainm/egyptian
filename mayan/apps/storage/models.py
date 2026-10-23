from pathlib import Path

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import (
    EventManagerMethodAfter, EventManagerSave
)

from .classes import DefinedStorageLazy
from .events import event_download_file_created, event_download_file_deleted
from .literals import (
    STORAGE_NAME_DOWNLOAD_FILE, STORAGE_NAME_SHARED_UPLOADED_FILE
)
from .managers import DownloadFileManager, SharedUploadedFileManager
from .model_mixins import (
    DatabaseFileModelMixin, DownloadFileBusinessLogicMixin
)
from .utils import download_file_upload_to, shared_uploaded_file_upload_to


class DownloadFile(
    DatabaseFileModelMixin, DownloadFileBusinessLogicMixin,
    ExtraDataModelMixin, models.Model
):
    _ordering_fields = ('filename', 'datetime', 'label')

    file = models.FileField(
        storage=DefinedStorageLazy(
            name=STORAGE_NAME_DOWNLOAD_FILE
        ), upload_to=download_file_upload_to, verbose_name=_(message='File')
    )
    label = models.CharField(
        db_index=True, max_length=192, verbose_name=_(message='Label')
    )
    user = models.ForeignKey(
        editable=False, on_delete=models.CASCADE,
        related_name='download_files', to=settings.AUTH_USER_MODEL,
        verbose_name=_(message='User')
    )

    objects = DownloadFileManager()

    class Meta:
        ordering = ('-datetime',)
        verbose_name = _(message='Download file')
        verbose_name_plural = _(message='Download files')

    def __str__(self):
        return str(self.filename or self.label)

    @method_event(
        event_manager_class=EventManagerMethodAfter,
        event=event_download_file_deleted
    )
    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(viewname='storage:download_file_list')

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'event': event_download_file_created,
            'target': 'self'
        }
    )
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class SharedUploadedFile(DatabaseFileModelMixin, models.Model):

    file = models.FileField(
        storage=DefinedStorageLazy(
            name=STORAGE_NAME_SHARED_UPLOADED_FILE
        ), upload_to=shared_uploaded_file_upload_to, verbose_name=_(
            message='File'
        )
    )
    filename = models.CharField(
        blank=True, max_length=255, verbose_name=_(message='Filename')
    )

    objects = SharedUploadedFileManager()

    class Meta:
        verbose_name = _(message='Shared uploaded file')
        verbose_name_plural = _(message='Shared uploaded files')

    def __str__(self):
        return self.filename

    def save(self, *args, **kwargs):
        path = self.file.name or ''
        self.filename = self.filename or Path(path).name
        super().save(*args, **kwargs)
        self.file.close()
