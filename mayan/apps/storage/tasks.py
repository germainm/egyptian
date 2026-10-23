import logging

from django.apps import apps
from django.db import OperationalError

from mayan.celery import app

logger = logging.getLogger(name=__name__)


@app.task(ignore_result=True)
def task_download_files_stale_delete():
    logger.debug(msg='Executing')

    DownloadFile = apps.get_model(
        app_label='storage', model_name='DownloadFile'
    )

    logger.debug('Start')

    DownloadFile.objects.stale_delete()

    logger.debug('Finished')


@app.task(ignore_result=True)
def task_shared_upload_stale_delete():
    logger.debug('Executing')

    SharedUploadedFile = apps.get_model(
        app_label='storage', model_name='SharedUploadedFile'
    )

    logger.debug('Start')

    SharedUploadedFile.objects.stale_delete()

    logger.debug('Finished')


@app.task(bind=True, ignore_result=True, retry_backoff=True)
def task_shared_upload_delete(self, shared_uploaded_file_id):
    SharedUploadedFile = apps.get_model(
        app_label='storage', model_name='SharedUploadedFile'
    )

    try:
        shared_uploaded_file = SharedUploadedFile.objects.get(
            pk=shared_uploaded_file_id
        )
    except SharedUploadedFile.DoesNotExist:
        logger.debug(
            'Shared uploaded file with ID: %s no longer exists. Nothing '
            'to delete.', shared_uploaded_file_id
        )
        return
    except OperationalError as exception:
        logger.warning(
            'Operational error attempting to load shared upload file '
            'with ID: %s; %s. Retrying.', shared_uploaded_file_id,
            exception
        )
        raise self.retry(exc=exception)

    try:
        shared_uploaded_file.delete()
    except OperationalError as exception:
        logger.warning(
            'Operational error attempting to delete shared upload file: '
            '%s; %s. Retrying.', shared_uploaded_file, exception
        )
        raise self.retry(exc=exception)
