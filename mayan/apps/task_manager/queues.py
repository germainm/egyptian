from django.utils.translation import gettext_lazy as _

from .classes import CeleryQueue, Worker
from .workers import worker_c

queue_default = CeleryQueue(
    default_queue=True, label=_(message='Default'), name='default',
    worker=Worker.get_default()
)

queue_task_manager_periodic = CeleryQueue(
    label=_(message='Task manager periodic'), name='task_manager_periodic',
    transient=True, worker=worker_c
)

task_type_deduplication_entry_stale_delete = queue_task_manager_periodic.add_task_type(
    dotted_path='mayan.apps.task_manager.tasks.task_deduplication_entry_stale_delete',
    label=_(message='Delete stale task deduplication markers'),
    name='task_deduplication_entry_stale_delete'
)
