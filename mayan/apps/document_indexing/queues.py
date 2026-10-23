from django.utils.translation import gettext_lazy as _

from mayan.apps.task_manager.classes import CeleryQueue
from mayan.apps.task_manager.task_deduplication_backends import (
    TaskDeduplicationBackendReleaseOnCompletion
)
from mayan.apps.task_manager.workers import worker_b, worker_c

queue_indexing = CeleryQueue(
    label=_(message='Indexing'), name='indexing', worker=worker_b
)
queue_indexing_slow = CeleryQueue(
    label=_(message='Indexing slow'), name='indexing_slow', worker=worker_c
)

queue_indexing.add_task_type(
    label=_(message='Remove document'),
    dotted_path='mayan.apps.document_indexing.tasks.task_index_instance_document_remove'
)
queue_indexing.add_task_type(
    deduplication_backend=TaskDeduplicationBackendReleaseOnCompletion,
    label=_(message='Index document'),
    dotted_path='mayan.apps.document_indexing.tasks.task_index_instance_document_add'
)

queue_indexing_slow.add_task_type(
    label=_(message='Rebuild index'),
    dotted_path='mayan.apps.document_indexing.tasks.task_index_template_rebuild'
)
