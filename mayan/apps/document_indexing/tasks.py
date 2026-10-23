import logging

from django.apps import apps
from django.db import OperationalError

from mayan.apps.lock_manager.exceptions import LockError
from mayan.apps.task_manager.task_classes import DeduplicatedTask
from mayan.celery import app

logger = logging.getLogger(name=__name__)



@app.task(
    base=DeduplicatedTask, bind=True, ignore_result=True, max_retries=None,
    retry_backoff=True, retry_backoff_max=60
)
def task_index_instance_document_add(
    self, document_id, index_instance_id=None
):
    Document = apps.get_model(
        app_label='documents', model_name='Document'
    )
    IndexInstance = apps.get_model(
        app_label='document_indexing', model_name='IndexInstance'
    )

    try:
        document = Document.objects.get(pk=document_id)
    except Document.DoesNotExist:
        """
        Document was deleted before we could execute, abort about updating.
        """
    else:
        try:
            if index_instance_id:
                index_instance = IndexInstance.objects.get(
                    pk=index_instance_id
                )
                index_instance.document_add(document=document)
            else:
                IndexInstance.objects.document_add(document=document)
        except OperationalError as exception:
            logger.warning(
                'Operational error while trying to index document: '
                '%s; %s', document, exception
            )
            raise self.retry(exc=exception)
        except LockError as exception:
            raise self.retry(exc=exception)


@app.task(
    bind=True, ignore_result=True, max_retries=None, retry_backoff=True
)
def task_index_instance_document_remove(self, document_id):
    Document = apps.get_model(
        app_label='documents', model_name='Document'
    )
    IndexInstance = apps.get_model(
        app_label='document_indexing', model_name='IndexInstance'
    )

    try:
        document = Document.objects.get(pk=document_id)
    except Document.DoesNotExist:
        try:
            IndexInstance.objects.delete_empty_nodes()
        except LockError as exception:
            raise self.retry(exc=exception)
    else:
        try:
            IndexInstance.objects.document_remove(document=document)
        except LockError as exception:
            raise self.retry(exc=exception)



@app.task(bind=True, ignore_result=True, retry_backoff=True)
def task_index_template_rebuild(self, index_id):
    IndexTemplate = apps.get_model(
        app_label='document_indexing', model_name='IndexTemplate'
    )

    try:
        index = IndexTemplate.objects.get(pk=index_id)
        index.rebuild()
    except LockError as exception:
        raise self.retry(exc=exception)
