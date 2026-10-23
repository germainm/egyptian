from django.utils.translation import gettext_lazy as _

from mayan.apps.task_manager.classes import CeleryQueue
from mayan.apps.task_manager.workers import worker_f

queue_file_metadata = CeleryQueue(
    label=_(message='File metadata'), name='file_metadata', worker=worker_f
)

queue_file_metadata.add_task_type(
    dotted_path='mayan.apps.file_metadata.tasks.task_document_file_metadata_process',
    label=_(message='Process document file')
)
queue_file_metadata.add_task_type(
    dotted_path='mayan.apps.file_metadata.tasks.task_document_file_metadata_finished',
    label=_(message='Finish document file metadata processing')
)
queue_file_metadata.add_task_type(
    dotted_path='mayan.apps.file_metadata.tasks.task_metadata_driver_process',
    label=_(message='Process file metadata driver')
)
