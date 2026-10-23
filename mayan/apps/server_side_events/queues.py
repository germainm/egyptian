from datetime import timedelta

from django.utils.translation import gettext_lazy as _

from mayan.apps.task_manager.classes import CeleryQueue
from mayan.apps.task_manager.workers import worker_e

from .literals import TASK_STREAM_EVENT_STALE_DELETE_INTERVAL

queue_server_side_events_periodic = CeleryQueue(
    label=_(message='Server side events periodic'),
    name='server_side_events_periodic', transient=True, worker=worker_e
)

queue_server_side_events_periodic.add_task_type(
    dotted_path='mayan.apps.server_side_events.tasks.task_stream_event_stale_delete',
    label=_(message='Delete stale stream events'),
    name='task_stream_event_stale_delete',
    schedule=timedelta(seconds=TASK_STREAM_EVENT_STALE_DELETE_INTERVAL)
)
