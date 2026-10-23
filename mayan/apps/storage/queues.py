from datetime import timedelta

from django.utils.translation import gettext_lazy as _

from mayan.apps.task_manager.classes import CeleryQueue
from mayan.apps.task_manager.workers import worker_b, worker_c

from .literals import (
    TASK_DOWNLOAD_FILE_STALE_INTERVAL, TASK_SHARED_UPLOADS_STALE_INTERVAL
)

queue_storage = CeleryQueue(
    label=_(message='Storage'), name='storage', worker=worker_b
)
queue_storage_periodic = CeleryQueue(
    label=_(message='Storage periodic'), name='storage_periodic', transient=True,
    worker=worker_c
)

queue_storage.add_task_type(
    dotted_path='mayan.apps.storage.tasks.task_shared_upload_delete',
    label=_(message='Delete a shared upload'), name='task_shared_upload_delete'
)

queue_storage_periodic.add_task_type(
    dotted_path='mayan.apps.storage.tasks.task_shared_upload_stale_delete',
    label=_(message='Delete stale uploads'), name='task_shared_upload_stale_delete',
    schedule=timedelta(
        seconds=TASK_SHARED_UPLOADS_STALE_INTERVAL
    )
)
queue_storage_periodic.add_task_type(
    dotted_path='mayan.apps.storage.tasks.task_download_files_stale_delete',
    label=_(message='Delete stale download files'),
    name='task_download_files_stale_delete',
    schedule=timedelta(
        seconds=TASK_DOWNLOAD_FILE_STALE_INTERVAL
    )
)
