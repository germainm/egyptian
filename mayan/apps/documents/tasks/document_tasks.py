import logging
from pathlib import Path

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import OperationalError

from mayan.celery import app

from .document_file_tasks import task_document_file_create
from .utils import execute_callback

logger = logging.getLogger(name=__name__)


@app.task(bind=True, ignore_result=True, retry_backoff=True)
def task_document_move_to_trash(self, document_id, user_id=None):
    Document = apps.get_model(
        app_label='documents', model_name='Document'
    )
    User = get_user_model()

    try:
        if user_id:
            user = User.objects.get(pk=user_id)
        else:
            user = None
    except OperationalError as exception:
        raise self.retry(exc=exception)

    logger.debug(msg='Executing')
    try:
        document = Document.valid.get(
            pk=document_id
        )
    except Document.DoesNotExist:
        logger.info(
            'Document with ID: %s is not a valid document. It was already '
            'moved to the trash or deleted.', document_id
        )
    except OperationalError as exception:
        raise self.retry(exc=exception)
    else:
        try:
            document._event_actor = user
            document.delete()
        except OperationalError as exception:
            raise self.retry(exc=exception)

    logger.debug(msg='Finished')


@app.task(bind=True, retry_backoff=True)
def task_document_upload(
    self, document_type_id, shared_uploaded_file_id,
    callback_dict=None, description=None, label=None, language=None,
    user_id=None
):
    callback_dict = callback_dict or {}

    DocumentType = apps.get_model(
        app_label='documents', model_name='DocumentType'
    )
    SharedUploadedFile = apps.get_model(
        app_label='storage', model_name='SharedUploadedFile'
    )
    User = get_user_model()

    try:
        document_type = DocumentType.objects.get(pk=document_type_id)
        shared_uploaded_file = SharedUploadedFile.objects.get(
            pk=shared_uploaded_file_id
        )
        if user_id:
            user = User.objects.get(pk=user_id)
        else:
            user = None
    except OperationalError as exception:
        raise self.retry(exc=exception)

    description = description or ''

    label = label or Path(
        str(shared_uploaded_file)
    ).name

    try:
        document = document_type.documents_create(
            description=description, label=label, language=language,
            user=user
        )
    except OperationalError as exception:
        logger.error(
            'Operational error creating new document of type: %s, '
            'label: %s; %s. Retrying.', document_type, label, exception
        )
        raise self.retry(exc=exception)
    except Exception as exception:
        logger.critical(
            'Unexpected exception while creating new document of type: %s, '
            'label: %s; %s', document_type, label, exception
        )
        raise
    else:
        execute_callback(
            callback_dict=callback_dict, document=document,
            name='post_document_create'
        )

        task_document_file_create.apply_async(
            kwargs={
                'callback_dict': callback_dict,
                'document_id': document.pk,
                'filename': label,
                'is_document_upload_sequence': True,
                'shared_uploaded_file_id': shared_uploaded_file_id,
                'user_id': user_id
            }
        )
