from django.shortcuts import get_object_or_404

from rest_framework.generics import (
    get_object_or_404 as rest_get_object_or_404
)

from mayan.apps.acls.models import AccessControlList
from mayan.apps.documents.models.document_models import Document
from mayan.apps.documents.permissions import permission_document_file_new
from mayan.apps.documents.tasks import task_document_upload

from ..interfaces import (
    SourceBackendActionInterface, SourceBackendActionInterfaceRequestRESTAPI,
    SourceBackendActionInterfaceRequestViewForm,
    SourceBackendActionInterfaceTask
)

from .arguments import (
    argument_document, argument_document_id, argument_document_id_optional
)
from .document_description_mixins import (
    SourceBackendActionMixinDocumentDescriptionInteractive
)
from .document_label_mixins import SourceBackendActionMixinLabelInteractive
from .document_language_mixins import (
    SourceBackendActionMixinLanguageInteractive
)
from .user_mixins import SourceBackendActionMixinUserInteractive


class SourceBackendActionMixinDocumentInteractive:
    class Interface:
        class Model(SourceBackendActionInterface):
            class Argument:
                document = argument_document

            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['document'] = self.context['document']

        class RESTAPI(SourceBackendActionInterfaceRequestRESTAPI):
            class Argument:
                document_id = argument_document_id

            def process_interface_context(self):
                super().process_interface_context()

                queryset = AccessControlList.objects.restrict_queryset(
                    queryset=Document.valid.all(),
                    permission=permission_document_file_new,
                    user=self.context['request'].user
                )

                self.action_kwargs['document'] = rest_get_object_or_404(
                    queryset=queryset, pk=self.context['document_id']
                )

        class Task(SourceBackendActionInterfaceTask):
            class Argument:
                document_id = argument_document_id

            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['document'] = Document.valid.get(
                    pk=self.context['document_id']
                )

        class View(SourceBackendActionInterfaceRequestViewForm):
            class Argument:
                document = argument_document

            def process_interface_context(self):
                super().process_interface_context()

                queryset = AccessControlList.objects.restrict_queryset(
                    queryset=Document.valid.all(),
                    permission=permission_document_file_new,
                    user=self.context['request'].user
                )

                self.action_kwargs['document'] = get_object_or_404(
                    klass=queryset, pk=self.context['document'].pk
                )

    def _background_task(self, document, **kwargs):
        result = super()._background_task(**kwargs)

        result['document'] = document

        return result

    def get_task_kwargs(self, document, **kwargs):
        result = super().get_task_kwargs(**kwargs)

        result['action_interface_kwargs']['document_id'] = document.pk

        return result


class SourceBackendActionMixinDocumentOptionalTaskOnly:
    class Interface:
        class Task(SourceBackendActionInterfaceTask):
            class Argument:
                document_id = argument_document_id_optional

            def process_interface_context(self):
                super().process_interface_context()

                document_id = self.context['document_id']

                if document_id:
                    self.action_kwargs['document'] = Document.valid.get(
                        pk=document_id
                    )

    def _background_task(self, document=None, **kwargs):
        result = super()._background_task(**kwargs)

        result['document'] = document

        return result

    def get_document_file_task_kwargs(
        self, server_upload_entry, document=None, **kwargs
    ):
        result = super().get_document_file_task_kwargs(
            server_upload_entry=server_upload_entry, **kwargs
        )

        if document:
            result['document_id'] = document.pk

        return result

    def get_task_kwargs(self, document=None, **kwargs):
        result = super().get_task_kwargs(**kwargs)

        if document:
            result['action_interface_kwargs']['document_id'] = document.pk

        return result


class SourceBackendActionMixinDocumentUploadBase:
    def _background_task(self, **kwargs):
        result = super()._background_task(**kwargs)

        if result:
            server_upload_entry_list = result.get(
                'server_upload_entry_list', ()
            )

            for server_upload_entry in server_upload_entry_list:
                document_task_kwargs = self.get_document_task_kwargs(
                    server_upload_entry=server_upload_entry, **kwargs
                )

                document_task_kwargs['shared_uploaded_file_id'] = server_upload_entry[
                    'shared_uploaded_file_id'
                ]

                task_document_upload.apply_async(
                    kwargs=document_task_kwargs
                )

    def get_document_task_kwargs(
        self, server_upload_entry, document_type, **kwargs
    ):
        result = super().get_document_task_kwargs(
            server_upload_entry=server_upload_entry,
            **kwargs
        )

        result['document_type_id'] = document_type.pk

        return result


class SourceBackendActionMixinDocumentUploadInteractive(
    SourceBackendActionMixinDocumentDescriptionInteractive,
    SourceBackendActionMixinLabelInteractive,
    SourceBackendActionMixinLanguageInteractive,
    SourceBackendActionMixinUserInteractive,
    SourceBackendActionMixinDocumentUploadBase
):
    pass


class SourceBackendActionMixinDocumentUploadInteractiveNot(
    SourceBackendActionMixinDocumentUploadBase
):
    pass
