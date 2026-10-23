from datetime import timedelta

from django.utils.translation import gettext_lazy as _

from mayan.apps.task_manager.classes import CeleryQueue
from mayan.apps.task_manager.task_deduplication_backends import (
    TaskDeduplicationBackendReleaseOnCompletion
)
from mayan.apps.task_manager.workers import worker_e

from .literals import TASK_SAVED_RESULTSET_EXPIRED_DELETE_INTERVAL

queue_search = CeleryQueue(
    label=_(message='Search'), name='search', worker=worker_e
)
queue_search_slow = CeleryQueue(
    label=_(message='Search slow'), name='search_slow', worker=worker_e
)

queue_search.add_task_type(
    dotted_path='mayan.apps.dynamic_search.tasks.task_deindex_instance',
    label=_(message='Remove a model instance from the search engine.'),
    name='task_deindex_instance'
)
queue_search.add_task_type(
    deduplication_backend=TaskDeduplicationBackendReleaseOnCompletion,
    dotted_path='mayan.apps.dynamic_search.tasks.task_index_instance',
    label=_(message='Index a model instance to the search engine.'),
    name='task_index_instance'
)
queue_search.add_task_type(
    dotted_path='mayan.apps.dynamic_search.tasks.task_index_instances',
    label=_(
        message='Index all instances of a search model to the search engine.'
    ), name='task_index_instances'
)
queue_search.add_task_type(
    dotted_path='mayan.apps.dynamic_search.tasks.task_index_related_instance_m2m',
    label=_(
        message='Index all related instances of a search model after a many '
        'to many event.'
    ), name='task_index_related_instance_m2m'
)
queue_search.add_task_type(
    dotted_path='mayan.apps.dynamic_search.tasks.task_saved_resultset_expired_delete',
    label=_(message='Delete expired saved resultsets'),
    name='task_saved_resultset_expired_delete',
    schedule=timedelta(seconds=TASK_SAVED_RESULTSET_EXPIRED_DELETE_INTERVAL)
)

queue_search_slow.add_task_type(
    dotted_path='mayan.apps.dynamic_search.tasks.task_reindex_backend',
    label=_(
        message='Reset the search backend indices and index all instances '
        'again.'
    ), name='task_reindex_backend'
)
