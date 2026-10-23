from django.utils.translation import gettext_lazy as _

from mayan.apps.task_manager.classes import CeleryQueue
from mayan.apps.task_manager.workers import worker_b, worker_d

queue_ocr = CeleryQueue(name='ocr', label=_(message='OCR'), worker=worker_b)
queue_ocr_slow = CeleryQueue(
    label=_(message='OCR slow'), name='ocr_slow', worker=worker_d
)

queue_ocr.add_task_type(
    dotted_path='mayan.apps.ocr.tasks.task_document_version_ocr_finished',
    label=_(message='Finish document version OCR')
)
queue_ocr.add_task_type(
    dotted_path='mayan.apps.ocr.tasks.task_document_version_ocr_process',
    label=_(message='Document version OCR')
)

queue_ocr_slow.add_task_type(
    dotted_path='mayan.apps.ocr.tasks.task_document_version_page_ocr_process',
    label=_(message='Document version page OCR')
)
