from datetime import timedelta
import logging
import shutil

from django.db import models
from django.utils.timezone import now

from .settings import (
    setting_download_file_expiration_interval,
    setting_shared_uploaded_file_expiration_interval
)
from .utils import TemporaryFile

logger = logging.getLogger(name=__name__)


class DownloadFileManager(models.Manager):
    def create_from_content_function(
        self, content_function, filename, label, binary=True, user=None
    ):
        if binary:
            temporary_file_mode = 'wb+'
            download_file_mode = 'wb'
        else:
            temporary_file_mode = 'w+'
            download_file_mode = 'w'

        with TemporaryFile(mode=temporary_file_mode) as temporary_file_object:
            content_function(file_object=temporary_file_object)

            temporary_file_object.seek(0)

            download_file = self.model(
                filename=filename, label=label, user=user
            )
            download_file._event_actor = user
            download_file.save()

            with download_file.open(mode=download_file_mode) as file_object:
                shutil.copyfileobj(
                    fdst=file_object, fsrc=temporary_file_object
                )

        return download_file

    def get_stale_queryset(self):
        return self.filter(
            datetime__lt=now() - timedelta(
                seconds=setting_download_file_expiration_interval.value
            )
        )

    def stale_delete(self):
        for stale in self.get_stale_queryset():
            try:
                stale.delete()
            except Exception as exception:
                logger.error(
                    'Unable to delete stale download file ID: %d; %s',
                    stale.pk, exception
                )


class SharedUploadedFileManager(models.Manager):
    def get_stale_queryset(self):
        return self.filter(
            datetime__lt=now() - timedelta(
                seconds=setting_shared_uploaded_file_expiration_interval.value
            )
        )

    def stale_delete(self):
        for stale in self.get_stale_queryset():
            try:
                stale.delete()
            except Exception as exception:
                logger.error(
                    'Unable to delete stale shared uploaded file ID: %d; %s',
                    stale.pk, exception
                )
