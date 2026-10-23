from datetime import timedelta

from django.utils.translation import gettext_lazy as _

from mayan.apps.task_manager.classes import CeleryQueue
from mayan.apps.task_manager.workers import worker_b, worker_c

from .settings import (
    setting_task_document_type_document_stubs_delete_interval,
    setting_task_document_type_document_trash_periods_check_interval,
    setting_task_trashed_document_delete_periods_check_interval
)

queue_documents_fast = CeleryQueue(
    name='documents_fast', label=_(message='Documents fast'), worker=worker_b
)
queue_documents_slow = CeleryQueue(
    name='documents_slow', label=_(message='Documents slow'), worker=worker_b
)
queue_documents_file = CeleryQueue(
    name='documents_file', label=_(message='Documents file'), worker=worker_b
)
queue_documents_file_slow = CeleryQueue(
    name='documents_file_slow', label=_(message='Documents file slow'),
    worker=worker_b
)
queue_documents_periodic = CeleryQueue(
    name='documents_periodic', label=_(message='Documents periodic'),
    transient=True, worker=worker_c
)
queue_documents_trash = CeleryQueue(
    name='documents_trash', label=_(message='Documents trash'),
    worker=worker_c
)
queue_documents_version = CeleryQueue(
    name='documents_version', label=_(message='Documents version'),
    worker=worker_b
)

queue_documents_fast.add_task_type(
    dotted_path='mayan.apps.documents.tasks.document_file_tasks.task_document_file_create',
    label=_(message='Create new document file')
)
queue_documents_slow.add_task_type(
    dotted_path='mayan.apps.documents.tasks.document_file_tasks.task_document_file_upload',
    label=_(message='Upload new document file')
)
queue_documents_slow.add_task_type(
    dotted_path='mayan.apps.documents.tasks.document_tasks.task_document_move_to_trash',
    label=_(message='Move a document to the trash')
)
queue_documents_slow.add_task_type(
    dotted_path='mayan.apps.documents.tasks.document_tasks.task_document_upload',
    label=_(message='Upload new document')
)

queue_documents_file.add_task_type(
    dotted_path='mayan.apps.documents.tasks.document_file_tasks.task_document_file_checksum_update',
    label=_(message='Calculate and update document file checksum')
)
queue_documents_file.add_task_type(
    dotted_path='mayan.apps.documents.tasks.document_file_tasks.task_document_file_mimetype_update',
    label=_(message='Calculate and update document file MIME type')
)
queue_documents_file.add_task_type(
    dotted_path='mayan.apps.documents.tasks.document_file_tasks.task_document_file_page_count_update',
    label=_(message='Update document file page count')
)
queue_documents_file.add_task_type(
    dotted_path='mayan.apps.documents.tasks.document_file_tasks.task_document_file_size_update',
    label=_(message='Update document file size')
)
queue_documents_file.add_task_type(
    dotted_path='mayan.apps.documents.tasks.document_file_tasks.task_document_file_version_create',
    label=_(message='Create a new version after the file is processed')
)

queue_documents_file_slow.add_task_type(
    dotted_path='mayan.apps.documents.tasks.document_file_tasks.task_document_file_delete',
    label=_(message='Delete a document file')
)

queue_documents_periodic.add_task_type(
    dotted_path='mayan.apps.documents.tasks.document_type_tasks.task_document_type_document_trash_periods_check',
    label=_(message='Check document type trash periods'),
    name='task_document_type_document_trash_periods_check',
    schedule=timedelta(
        seconds=setting_task_document_type_document_trash_periods_check_interval.value
    )
)
queue_documents_periodic.add_task_type(
    dotted_path='mayan.apps.documents.tasks.document_type_tasks.task_document_type_document_stubs_delete',
    label=_(message='Delete document stubs'),
    name='task_document_type_document_stubs_delete',
    schedule=timedelta(
        seconds=setting_task_document_type_document_stubs_delete_interval.value
    )
)
queue_documents_periodic.add_task_type(
    dotted_path='mayan.apps.documents.tasks.document_type_tasks.task_document_type_trashed_document_delete_periods_check',
    label=_(message='Check document type delete periods'),
    name='task_document_type_trashed_document_delete_periods_check',
    schedule=timedelta(
        seconds=setting_task_trashed_document_delete_periods_check_interval.value
    )
)

queue_documents_trash.add_task_type(
    dotted_path='mayan.apps.documents.tasks.trashed_document_tasks.task_trash_can_empty',
    label=_(message='Empty the trash can')
)
queue_documents_trash.add_task_type(
    dotted_path='mayan.apps.documents.tasks.trashed_document_tasks.task_trashed_document_delete',
    label=_(message='Delete a document')
)

queue_documents_version.add_task_type(
    dotted_path='mayan.apps.documents.tasks.document_version_tasks.task_document_version_page_list_append',
    label=_(message='Append all document file pages to a document version')
)
queue_documents_version.add_task_type(
    dotted_path='mayan.apps.documents.tasks.document_version_tasks.task_document_version_page_list_reset',
    label=_(message='Reset the page list of a document version')
)
queue_documents_version.add_task_type(
    dotted_path='mayan.apps.documents.tasks.document_version_tasks.task_document_version_export',
    label=_(message='Export a document version to a download file')
)
queue_documents_version.add_task_type(
    dotted_path='mayan.apps.documents.tasks.document_version_tasks.task_document_version_delete',
    label=_(message='Delete a document version')
)
