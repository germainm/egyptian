from mayan.apps.documents.permissions import (
    permission_document_create, permission_document_file_new
)
from mayan.apps.source_compressed.source_backend_actions.mixins import (
    SourceBackendActionMixinCompressedInteractive
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
from mayan.apps.sources.source_backend_actions.mixins.immediate_mode_mixins import (
    SourceBackendActionMixinImmediateMode
)

from .callback_mixins import (
    SourceBackendActionMixinCallbackDocumentFileUploadInteractive,
    SourceBackendActionMixinCallbackDocumentUploadInteractive
)
from .file_mixins import SourceBackendActionMixinFileUser


class SourceBackendActionInteractiveBase(
    SourceBackendActionMixinFileUser, SourceBackendAction
):
    pass


class SourceBackendActionInteractiveDocumentFileUpload(
    SourceBackendActionMixinDocumentFileUploadInteractive,
    SourceBackendActionMixinDocumentInteractive,
    SourceBackendActionMixinCallbackDocumentFileUploadInteractive,
    SourceBackendActionInteractiveBase
):
    name = 'document_file_upload'
    permission = permission_document_file_new


class SourceBackendActionInteractiveDocumentUpload(
    SourceBackendActionMixinDocumentUploadInteractive,
    SourceBackendActionMixinCompressedInteractive,
    SourceBackendActionMixinImmediateMode,
    SourceBackendActionMixinCallbackDocumentUploadInteractive,
    SourceBackendActionMixinDocumentTypeInteractive,
    SourceBackendActionInteractiveBase
):
    name = 'document_upload'
    permission = permission_document_create
