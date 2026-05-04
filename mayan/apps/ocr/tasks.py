import logging

from celery import chord

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import OperationalError

from mayan.apps.lock_manager.exceptions import LockError
from mayan.celery import app

logger = logging.getLogger(name=__name__)


@app.task(bind=True, ignore_result=True, retry_backoff=True)
def task_document_version_ocr_process(
    self, document_version_id, user_id=None
):
    logger.debug(
        'Starting OCR for document version page ID: %s', document_version_id
    )
    DocumentVersion = apps.get_model(
        app_label='documents', model_name='DocumentVersion'
    )

    document_version = DocumentVersion.objects.get(
        pk=document_version_id
    )

    document_version_page_tasks = []
    for document_version_page in document_version.pages.all():
        document_version_page_tasks.append(
            task_document_version_page_ocr_process.s(
                document_version_page_id=document_version_page.pk,
                user_id=user_id
            )
        )

    chord(document_version_page_tasks)(
        task_document_version_ocr_finished.s(
            document_version_id=document_version.pk, user_id=user_id
        )
    )


@app.task(bind=True, retry_backoff=True)
def task_document_version_page_ocr_process(
    self, document_version_page_id, user_id=None
):
    CachePartitionFile = apps.get_model(
        app_label='file_caching', model_name='CachePartitionFile'
    )
    DocumentVersionPageOCRContent = apps.get_model(
        app_label='ocr', model_name='DocumentVersionPageOCRContent'
    )
    DocumentVersionPage = apps.get_model(
        app_label='documents', model_name='DocumentVersionPage'
    )
    document_version_page = DocumentVersionPage.objects.get(
        pk=document_version_page_id
    )

    User = get_user_model()

    if user_id:
        user = User.objects.get(pk=user_id)
    else:
        user = None

    try:
        DocumentVersionPageOCRContent.objects.process_document_version_page(
            document_version_page=document_version_page,
            user=user
        )
    except CachePartitionFile.DoesNotExist as exception:
        logger.debug(
            'Document version page image not found. Possible cause '
            'overloaded system or cache size too small. Retrying task.',
        )
        raise self.retry(exc=exception)
    except LockError as exception:
        raise self.retry(exc=exception)
    except (OperationalError, FileNotFoundError) as exception:
        raise self.retry(exc=exception)


@app.task(bind=True, ignore_result=True)
def task_document_version_ocr_finished(
    self, results, document_version_id, user_id=None
):
    logger.debug(
        'OCR complete for document version ID: %s', document_version_id
    )

    DocumentVersion = apps.get_model(
        app_label='documents', model_name='DocumentVersion'
    )
    DocumentVersionPageOCRContent = apps.get_model(
        app_label='ocr', model_name='DocumentVersionPageOCRContent'
    )

    document_version = DocumentVersion.objects.get(pk=document_version_id)

    User = get_user_model()

    if user_id:
        user = User.objects.get(pk=user_id)
    else:
        user = None

    try:
        DocumentVersionPageOCRContent.objects.do_ocr_finished(
            document_version=document_version,
            user=user
        )
    except (OperationalError, FileNotFoundError) as exception:
        logger.warning(
            'Operational error in OCR finish for document version: %d; %s. '
            'Retrying.', document_version, exception
        )
        raise self.retry(exc=exception)

