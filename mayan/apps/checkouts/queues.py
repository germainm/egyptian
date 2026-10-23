from datetime import timedelta

from django.utils.translation import gettext_lazy as _

from mayan.apps.task_manager.classes import CeleryQueue
from mayan.apps.task_manager.workers import worker_e

from .literals import CHECK_EXPIRED_CHECK_OUTS_INTERVAL

queue_checkouts_periodic = CeleryQueue(
    label=_(message='Checkouts periodic'), name='checkouts_periodic', transient=True,
    worker=worker_e
)

queue_checkouts_periodic.add_task_type(
    label=_(message='Check expired checkouts'),
    name='task_check_expired_check_outs',
    dotted_path='mayan.apps.checkouts.tasks.task_check_expired_check_outs',
    schedule=timedelta(
        seconds=CHECK_EXPIRED_CHECK_OUTS_INTERVAL
    )
)
