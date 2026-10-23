from datetime import timedelta

from django.utils.translation import gettext_lazy as _

from mayan.apps.task_manager.classes import CeleryQueue
from mayan.apps.task_manager.workers import worker_e

from .settings import setting_login_attempt_retention_task_interval

queue_authentication_attempts = CeleryQueue(
    label=_(message='Authentication attempts'),
    name='authentication_attempts', transient=True, worker=worker_e
)

queue_authentication_attempts.add_task_type(
    dotted_path='mayan.apps.authentication_attempts.tasks.task_login_attempt_retention',
    label=_(message='Launch the login attempt retention backend'),
    name='task_login_attempt_retention',
    schedule=timedelta(
        seconds=setting_login_attempt_retention_task_interval.value
    )
)
