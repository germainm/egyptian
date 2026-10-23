from django.utils.translation import gettext_lazy as _

from mayan.apps.task_manager.classes import CeleryQueue
from mayan.apps.task_manager.workers import worker_c

queue_statistics = CeleryQueue(
    label=_(message='Statistics'), name='statistics', transient=True,
    worker=worker_c
)

queue_task_execute_statistic = queue_statistics.add_task_type(
    label=_(message='Execute statistic'),
    dotted_path='mayan.apps.mayan_statistics.tasks.task_execute_statistic'
)
