from datetime import timedelta

from django.utils.translation import gettext_lazy as _

from mayan.apps.task_manager.classes import CeleryQueue
from mayan.apps.task_manager.workers import worker_b, worker_c

from .settings import setting_event_prune_task_interval

queue_events_fast = CeleryQueue(
    label=_(message='Events fast'), name='events_fast', worker=worker_b
)
queue_events_slow = CeleryQueue(
    label=_(message='Events slow'), name='events_slow', transient=True,
    worker=worker_c
)

queue_events_fast.add_task_type(
    dotted_path='mayan.apps.events.tasks.task_event_commit',
    label=_(message='Commit an event'), name='task_event_commit'
)

queue_events_slow.add_task_type(
    dotted_path='mayan.apps.events.tasks.task_event_prune',
    label=_(message='Launch the event prune backend'),
    name='task_event_prune',
    schedule=timedelta(seconds=setting_event_prune_task_interval.value),
)
queue_events_slow.add_task_type(
    dotted_path='mayan.apps.events.tasks.task_event_queryset_clear',
    label=_(message='Clear event querysets'),
    name='task_event_queryset_clear'
)
queue_events_slow.add_task_type(
    dotted_path='mayan.apps.events.tasks.task_event_queryset_export',
    label=_(message='Export event querysets'),
    name='task_event_queryset_export'
)
