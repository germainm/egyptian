from django.utils.translation import gettext_lazy as _

from mayan.apps.task_manager.classes import CeleryQueue
from mayan.apps.task_manager.workers import worker_b, worker_c

queue_file_caching = CeleryQueue(
    name='file_caching', label=_(message='File caching'), worker=worker_b
)
queue_file_caching_slow = CeleryQueue(
    name='file_caching_slow', label=_(message='File caching slow'), worker=worker_c
)

queue_file_caching.add_task_type(
    dotted_path='mayan.apps.file_caching.tasks.task_cache_partition_purge',
    label=_(message='Purge a file cache partition')
)
queue_file_caching.add_task_type(
    dotted_path='mayan.apps.file_caching.tasks.task_cache_prune',
    label=_(message='Prune a file cache to a smaller size')
)

queue_file_caching_slow.add_task_type(
    dotted_path='mayan.apps.file_caching.tasks.task_cache_purge',
    label=_(message='Purge a file cache')
)
