from mayan.apps.documents.permissions import (
    permission_document_create, permission_document_file_new
)
from mayan.apps.source_interactive.source_backend_actions.callback_mixins import (
    SourceBackendActionMixinCallbackDocumentFileUploadInteractive,
    SourceBackendActionMixinCallbackDocumentUploadInteractive
)
from mayan.apps.sources.source_backend_actions.base import SourceBackendAction
from mayan.apps.sources.source_backend_actions.mixins.document_file_mixins import (
    SourceBackendActionMixinDocumentFileUploadInteractive
)
from mayan.apps.sources.source_backend_actions.mixins.document_mixins import (
    SourceBackendActionMixinDocumentInteractive,
    SourceBackendActionMixinDocumentUploadInteractive
)
from mayan.apps.sources.source_backend_actions.mixins.document_type_mixins import (
    SourceBackendActionMixinDocumentTypeInteractive
)

from .mixins import SourceBackendActionMixinFileGenerated


class SourceBackendActionGenerateFileBase(
    SourceBackendActionMixinFileGenerated, SourceBackendAction
):
    pass


class SourceBackendActionGenerateFileDocumentFileUpload(
    SourceBackendActionMixinDocumentFileUploadInteractive,
    SourceBackendActionMixinCallbackDocumentFileUploadInteractive,
    SourceBackendActionMixinDocumentInteractive,
    SourceBackendActionGenerateFileBase
):
    name = 'document_file_upload'
    permission = permission_document_file_new


class SourceBackendActionGenerateFileDocumentUpload(
    SourceBackendActionMixinDocumentUploadInteractive,
    SourceBackendActionMixinCallbackDocumentUploadInteractive,
    SourceBackendActionMixinDocumentTypeInteractive,
    SourceBackendActionGenerateFileBase
):
    name = 'document_upload'
    permission = permission_document_create
