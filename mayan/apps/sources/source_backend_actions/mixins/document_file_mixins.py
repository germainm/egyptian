from mayan.apps.documents.tasks import task_document_file_create

from .document_file_action_mixins import (
    SourceBackendActionMixinDocumentFileActionInteractive
)
from .document_file_comment_mixins import (
    SourceBackendActionMixinDocumentFileCommentInteractive
)
from .document_file_filename_mixins import (
    SourceBackendActionMixinDocumentFileFilenameInteractive
)
from .user_mixins import SourceBackendActionMixinUserInteractive


class SourceBackendActionMixinDocumentFileUploadInteractiveBase:
    def _background_task(self, **kwargs):
        result = super()._background_task(**kwargs)
        document = result['document']

        for server_upload_entry in result['server_upload_entry_list']:
            document_file_task_kwargs = self.get_document_file_task_kwargs(
                server_upload_entry=server_upload_entry, **kwargs
            )

            document_file_task_kwargs['shared_uploaded_file_id'] = server_upload_entry[
                'shared_uploaded_file_id'
            ]
            document_file_task_kwargs['document_id'] = document.pk

            task_document_file_create.apply_async(
                kwargs=document_file_task_kwargs
            )

    def get_document_file_task_kwargs(self, **kwargs):
        result = super().get_document_file_task_kwargs(**kwargs)

        result['is_document_upload_sequence'] = True

        return result

    def get_task_kwargs(self, **kwargs):
        result = super().get_task_kwargs(**kwargs)

        return result


class SourceBackendActionMixinDocumentFileUploadInteractive(
    SourceBackendActionMixinDocumentFileActionInteractive,
    SourceBackendActionMixinDocumentFileCommentInteractive,
    SourceBackendActionMixinDocumentFileFilenameInteractive,
    SourceBackendActionMixinUserInteractive,
    SourceBackendActionMixinDocumentFileUploadInteractiveBase
):
    pass
