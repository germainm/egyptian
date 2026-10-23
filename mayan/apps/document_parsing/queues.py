from django.utils.translation import gettext_lazy as _

from mayan.apps.task_manager.classes import CeleryQueue
from mayan.apps.task_manager.workers import worker_c

queue_parsing = CeleryQueue(
    name='parsing', label=_(message='Parsing'), worker=worker_c
)

queue_parsing.add_task_type(
    dotted_path='mayan.apps.document_parsing.tasks.task_parse_document_file',
    label=_(message='Document file parsing')
)
