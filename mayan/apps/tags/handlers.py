import logging

from mayan.apps.document_indexing.tasks import (
    task_index_instance_document_add
)

logger = logging.getLogger(name=__name__)


def handler_index_document(sender, **kwargs):
    if not kwargs.get('created', False):
        for document in kwargs['instance'].documents.all():
            task_index_instance_document_add.apply_async(
                kwargs={'document_id': document.pk}
            )


def handler_tag_pre_delete(sender, **kwargs):
    for document in kwargs['instance'].documents.all():
        kwargs['instance']._remove_from(document=document)
