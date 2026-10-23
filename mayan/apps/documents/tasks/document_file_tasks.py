import logging
from pathlib import Path

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.files import File
from django.db import OperationalError

from mayan.apps.storage.tasks import task_shared_upload_delete
from mayan.celery import app

from ..literals import DEFAULT_DOCUMENT_FILE_ACTION_NAME

from .utils import execute_callback

logger = logging.getLogger(name=__name__)


@app.task(bind=True, ignore_result=True, retry_backoff=True)
def task_document_file_checksum_update(
    self, document_file_id, action_name=None, callback_dict=None,
    is_document_upload_sequence=False, user_id=None
):
    callback_dict = callback_dict or {}

    DocumentFile = apps.get_model(
        app_label='documents', model_name='DocumentFile'
    )

    try:
        document_file = DocumentFile.objects.get(pk=document_file_id)
    except OperationalError as exception:
        raise self.retry(exc=exception)

    try:
        document_file.checksum_update(save=False)
        document_file._event_ignore = True
        document_file.save(
            update_fields=('checksum',)
        )
    except OperationalError as exception:
        logger.warning(
            'Operational error during attempt to update the checksum for '
            'document file: %s; %s. Retrying.', document_file,
            exception
        )
        raise self.retry(exc=exception)
    except Exception as exception:
        logger.critical(
            'Unexpected exception when updating checksum for document '
            'file: %s; %s.', document_file, exception
        )
        raise
    else:
        if is_document_upload_sequence:
            task_document_file_mimetype_update.apply_async(
                kwargs={
                    'action_name': action_name,
                    'callback_dict': callback_dict,
                    'document_file_id': document_file.pk,
                    'is_document_upload_sequence': is_document_upload_sequence,
                    'user_id': user_id
                }
            )


@app.task(bind=True, ignore_result=True, retry_backoff=True)
def task_document_file_create(
    self, document_id, shared_uploaded_file_id, action_name=None,
    callback_dict=None, comment=None, filename=None,
    is_document_upload_sequence=False, user_id=None
):
    callback_dict = callback_dict or {}

    Document = apps.get_model(
        app_label='documents', model_name='Document'
    )
    DocumentFile = apps.get_model(
        app_label='documents', model_name='DocumentFile'
    )
    SharedUploadedFile = apps.get_model(
        app_label='storage', model_name='SharedUploadedFile'
    )
    User = get_user_model()

    action_name = action_name or DEFAULT_DOCUMENT_FILE_ACTION_NAME

    try:
        document = Document.objects.get(pk=document_id)
        shared_uploaded_file = SharedUploadedFile.objects.get(
            pk=shared_uploaded_file_id
        )

        if user_id:
            user = User.objects.get(pk=user_id)
        else:
            user = None
    except OperationalError as exception:
        raise self.retry(exc=exception)

    comment = comment or ''
    filename = filename or Path(
        str(shared_uploaded_file)
    ).name

    with shared_uploaded_file.open() as file_object:
        try:
            document_file = DocumentFile(
                comment=comment, document=document,
                file=File(file=file_object), filename=filename
            )
            document_file._event_actor = user
            document_file.save(skip_introspection=True)
        except OperationalError as exception:
            logger.warning(
                'Operational error while uploading new file for '
                'document: %s; %s. Retrying.', document, exception
            )
            raise self.retry(exc=exception)
        except Exception as exception:
            logger.critical(
                'Unexpected exception when uploading new file for '
                'document: %s; %s.', document, exception
            )
            raise
        else:
            task_shared_upload_delete.apply_async(
                kwargs={
                    'shared_uploaded_file_id': shared_uploaded_file.pk
                }
            )

            execute_callback(
                callback_dict=callback_dict, document_file=document_file,
                name='post_document_file_create'
            )

            task_document_file_size_update.apply_async(
                kwargs={
                    'action_name': action_name,
                    'callback_dict': callback_dict,
                    'document_file_id': document_file.pk,
                    'is_document_upload_sequence': is_document_upload_sequence,
                    'user_id': user_id
                }
            )


@app.task(bind=True, ignore_result=True, retry_backoff=True)
def task_document_file_delete(self, document_file_id, user_id=None):
    DocumentFile = apps.get_model(
        app_label='documents', model_name='DocumentFile'
    )
    User = get_user_model()

    try:
        if user_id:
            user = User.objects.get(pk=user_id)
        else:
            user = None

        document_file = DocumentFile.objects.get(
            pk=document_file_id
        )
    except OperationalError as exception:
        raise self.retry(exc=exception)

    try:
        document_file._event_actor = user
        document_file._event_keep_attributes = ('_event_actor',)
        document_file.delete()
    except OperationalError as exception:
        raise self.retry(exc=exception)


@app.task(bind=True, ignore_result=True, retry_backoff=True)
def task_document_file_mimetype_update(
    self, document_file_id, action_name=None, callback_dict=None,
    is_document_upload_sequence=False, user_id=None
):
    callback_dict = callback_dict or {}

    DocumentFile = apps.get_model(
        app_label='documents', model_name='DocumentFile'
    )

    try:
        document_file = DocumentFile.objects.get(pk=document_file_id)
    except OperationalError as exception:
        raise self.retry(exc=exception)

    try:
        document_file.mimetype_update(save=False)
        document_file._event_ignore = True
        document_file.save(
            update_fields=('encoding', 'mimetype',)
        )
    except OperationalError as exception:
        logger.warning(
            'Operational error during attempt to update the MIME type of '
            'document file: %s; %s. Retrying.', document_file, exception
        )
        raise self.retry(exc=exception)
    except Exception as exception:
        logger.critical(
            'Unexpected exception when updating the MIME type of document '
            'file: %s; %s.', document_file, exception
        )
        raise
    else:
        if is_document_upload_sequence:
            task_document_file_page_count_update.apply_async(
                kwargs={
                    'action_name': action_name,
                    'callback_dict': callback_dict,
                    'document_file_id': document_file.pk,
                    'is_document_upload_sequence': is_document_upload_sequence,
                    'user_id': user_id
                }
            )


@app.task(bind=True, ignore_result=True, retry_backoff=True)
def task_document_file_page_count_update(
    self, document_file_id, action_name=None, callback_dict=None,
    is_document_upload_sequence=False, user_id=None
):
    callback_dict = callback_dict or {}

    DocumentFile = apps.get_model(
        app_label='documents', model_name='DocumentFile'
    )
    User = get_user_model()

    try:
        document_file = DocumentFile.objects.get(pk=document_file_id)

        if user_id:
            user = User.objects.get(pk=user_id)
        else:
            user = None
    except OperationalError as exception:
        raise self.retry(exc=exception)

    try:
        document_file.page_count_update(user=user)
    except OperationalError as exception:
        logger.warning(
            'Operational error during attempt to update the page count for '
            'document file: %s; %s. Retrying.', document_file,
            exception
        )
        raise self.retry(exc=exception)
    except Exception as exception:
        logger.critical(
            'Unexpected exception updating the page count of document '
            'file: %s; %s.', document_file, exception
        )
        raise
    else:
        document_file.upload_complete()

        if is_document_upload_sequence:
            task_document_file_version_create.apply_async(
                kwargs={
                    'action_name': action_name,
                    'document_file_id': document_file.pk,
                    'user_id': user_id
                }
            )

            execute_callback(
                callback_dict=callback_dict, document_file=document_file,
                name='post_document_file_upload'
            )


@app.task(bind=True, ignore_result=True, retry_backoff=True)
def task_document_file_size_update(
    self, document_file_id, action_name=None, callback_dict=None,
    is_document_upload_sequence=False, user_id=None
):
    callback_dict = callback_dict or {}

    DocumentFile = apps.get_model(
        app_label='documents', model_name='DocumentFile'
    )

    try:
        document_file = DocumentFile.objects.get(pk=document_file_id)
    except OperationalError as exception:
        raise self.retry(exc=exception)

    try:
        document_file.size_update(save=False)
        document_file._event_ignore = True
        document_file.save(
            update_fields=('size',)
        )
    except OperationalError as exception:
        logger.warning(
            'Operational error during attempt to update the size for'
            'document file: %s; %s. Retrying.', document_file,
            exception
        )
        raise self.retry(exc=exception)
    except Exception as exception:
        logger.critical(
            'Unexpected exception updating the size document '
            'file: %s; %s.', document_file, exception
        )
        raise
    else:
        if is_document_upload_sequence:
            task_document_file_checksum_update.apply_async(
                kwargs={
                    'action_name': action_name,
                    'callback_dict': callback_dict,
                    'document_file_id': document_file.pk,
                    'is_document_upload_sequence': is_document_upload_sequence,
                    'user_id': user_id
                }
            )


@app.task(ignore_result=True)
def task_document_file_upload(
    document_id, shared_uploaded_file_id, action_name=None,
    callback_dict=None, comment=None, filename=None, user_id=None
):
    callback_dict = callback_dict or {}

    task_document_file_create.apply_async(
        kwargs={
            'action_name': action_name,
            'callback_dict': callback_dict,
            'comment': comment,
            'document_id': document_id,
            'filename': filename,
            'is_document_upload_sequence': True,
            'shared_uploaded_file_id': shared_uploaded_file_id,
            'user_id': user_id
        }
    )


@app.task(bind=True, ignore_result=True, retry_backoff=True)
def task_document_file_version_create(
    self, action_name, document_file_id, comment=None, user_id=None
):
    DocumentFile = apps.get_model(
        app_label='documents', model_name='DocumentFile'
    )
    User = get_user_model()

    try:
        document_file = DocumentFile.objects.get(
            pk=document_file_id
        )

        if user_id:
            user = User.objects.get(pk=user_id)
        else:
            user = None
    except OperationalError as exception:
        raise self.retry(exc=exception)

    comment = comment or ''

    try:
        document_file.versions_new(
            action_name=action_name, comment=comment, user=user
        )
    except OperationalError as exception:
        logger.warning(
            'Operational error during attempt execute the document version '
            'action: %s for %s; %s. Retrying.', action_name, document_file,
            exception
        )
        raise self.retry(exc=exception)
