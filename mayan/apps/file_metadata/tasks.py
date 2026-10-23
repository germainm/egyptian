import logging

from celery import chord

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import OperationalError

from mayan.apps.lock_manager.backends.base import LockingBackend
from mayan.apps.lock_manager.exceptions import LockBackendError, LockError
from mayan.celery import app

from .classes import FileMetadataDriver
from .events import event_file_metadata_document_file_finished
from .literals import (
    LOCK_EXPIRE, RETRY_BACKOFF, RETRY_BACKOFF_MAX, RETRY_JITTER,
    TASK_METADATA_DRIVER_PROCESS_LOCK_NAME_TEMPLATE
)
from .utils import get_stored_driver_id_list

logger = logging.getLogger(name=__name__)


@app.task(
    autoretry_for=(OperationalError,), bind=True, ignore_result=True,
    retry_backoff=RETRY_BACKOFF, retry_backoff_max=RETRY_BACKOFF_MAX,
    retry_jitter=RETRY_JITTER
)
def task_document_file_metadata_process(
    self, document_file_id, user_id=None
):
    DocumentFile = apps.get_model(
        app_label='documents', model_name='DocumentFile'
    )

    try:
        document_file = DocumentFile.objects.get(pk=document_file_id)
    except DocumentFile.DoesNotExist:
        return
    else:
        driver_class_list = FileMetadataDriver.collection.get_driver_for_mime_type(
            mime_type=document_file.mimetype
        )

        document_type = document_file.document.document_type

        stored_driver_id_list = get_stored_driver_id_list(
            document_type=document_type, driver_class_list=driver_class_list
        )

        document_file_metadata_driver_task_list = [
            task_metadata_driver_process.s(
                document_file_id=document_file_id,
                stored_driver_id=stored_driver_id
            ) for stored_driver_id in stored_driver_id_list
        ]

        if document_file_metadata_driver_task_list:
            chord(document_file_metadata_driver_task_list)(
                task_document_file_metadata_finished.s(
                    document_file_id=document_file_id, user_id=user_id
                )
            )
        else:
            task_document_file_metadata_finished.apply_async(
                kwargs={
                    'document_file_id': document_file_id, 'results': [],
                    'user_id': user_id
                }
            )


@app.task(
    autoretry_for=(OperationalError,), bind=True, ignore_result=True,
    retry_backoff=RETRY_BACKOFF, retry_backoff_max=RETRY_BACKOFF_MAX,
    retry_jitter=RETRY_JITTER
)
def task_document_file_metadata_finished(
    self, results, document_file_id, user_id=None
):
    DocumentFile = apps.get_model(
        app_label='documents', model_name='DocumentFile'
    )

    User = get_user_model()

    try:
        document_file = DocumentFile.objects.get(pk=document_file_id)
    except DocumentFile.DoesNotExist:
        return
    else:
        user = None

        if user_id:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                """
                User does not exist.
                Committing the file event without an actor.
                """

        event_file_metadata_document_file_finished.commit(
            action_object=document_file.document, actor=user,
            target=document_file
        )


@app.task(
    autoretry_for=(LockBackendError, OperationalError), bind=True,
    ignore_result=False, retry_backoff=RETRY_BACKOFF,
    retry_backoff_max=RETRY_BACKOFF_MAX, retry_jitter=RETRY_JITTER
)
def task_metadata_driver_process(self, document_file_id, stored_driver_id):
    DocumentFile = apps.get_model(
        app_label='documents', model_name='DocumentFile'
    )
    StoredDriver = apps.get_model(
        app_label='file_metadata', model_name='StoredDriver'
    )

    try:
        document_file = DocumentFile.objects.get(pk=document_file_id)
    except DocumentFile.DoesNotExist:
        return
    else:
        try:
            stored_driver = StoredDriver.objects.get(pk=stored_driver_id)
        except StoredDriver.DoesNotExist:
            logger.warning(
                'Stored driver with ID: %s, does not exist. Skipping file '
                'metadata driver processing.', stored_driver_id
            )
            return
        else:
            lock_id = TASK_METADATA_DRIVER_PROCESS_LOCK_NAME_TEMPLATE.format(
                document_file_id=document_file_id,
                stored_driver_id=stored_driver_id
            )

            logger.debug('trying to acquire lock: %s', lock_id)

            try:
                locking_backend = LockingBackend.get_backend()
                lock = locking_backend.acquire_lock(
                    name=lock_id, timeout=LOCK_EXPIRE
                )
            except LockBackendError:
                logger.warning(
                    'Lock backend error acquiring lock: %s. Retrying.',
                    lock_id
                )
                raise
            except LockError:
                logger.info(
                    'Unable to acquire lock: %s. The document file is '
                    'already being processed by this driver. Skipping.',
                    lock_id
                )
                return
            else:
                logger.debug('acquired lock: %s', lock_id)

                try:
                    driver_class = stored_driver.driver_class
                    driver_class.do_document_file_process(
                        document_file=document_file
                    )
                finally:
                    try:
                        lock.release()
                    except Exception as exception:
                        logger.error(
                            'Unhandled exception releasing lock: %s; %s',
                            lock_id, exception, exc_info=True
                        )
