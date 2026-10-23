from django.utils.translation import gettext_lazy as _

from mayan.apps.task_manager.classes import CeleryQueue
from mayan.apps.task_manager.workers import worker_c, worker_f

queue_signatures = CeleryQueue(
    label=_(message='Signatures'), name='signatures', worker=worker_c
)
queue_signatures_slow = CeleryQueue(
    label=_(message='Signatures slow'), name='signatures_slow', worker=worker_f
)

queue_signatures.add_task_type(
    dotted_path='mayan.apps.document_signatures.tasks.task_verify_key_signatures',
    label=_(message='Verify key signatures')
)
queue_signatures.add_task_type(
    dotted_path='mayan.apps.document_signatures.tasks.task_unverify_key_signatures',
    label=_(message='Unverify key signatures')
)
queue_signatures.add_task_type(
    dotted_path='mayan.apps.document_signatures.tasks.task_verify_document_file',
    label=_(message='Verify document file')
)

queue_signatures_slow.add_task_type(
    dotted_path='mayan.apps.document_signatures.tasks.task_verify_missing_embedded_signature',
    label=_(message='Verify missing embedded signature')
)
queue_signatures_slow.add_task_type(
    dotted_path='mayan.apps.document_signatures.tasks.task_refresh_signature_information',
    label=_(message='Refresh existing signature information')
)
