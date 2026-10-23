from rest_framework import status
from rest_framework.response import Response

from mayan.apps.documents.serializers.document_serializers import (
    DocumentSerializer
)
from mayan.apps.documents.tasks import task_document_file_create

from ..interfaces import (
    SourceBackendActionInterface, SourceBackendActionInterfaceRequestRESTAPI,
    SourceBackendActionInterfaceRequestViewForm,
    SourceBackendActionInterfaceTask
)

from .arguments import (
    argument_immediate_mode_optional, argument_immediate_mode_required
)
from .document_mixins import SourceBackendActionMixinDocumentOptionalTaskOnly
from .literals import DEFAULT_IMMEDIATE_MODE


class SourceBackendActionMixinImmediateMode(SourceBackendActionMixinDocumentOptionalTaskOnly):
    class Interface:
        class Model(SourceBackendActionInterface):
            class Argument:
                immediate_mode = argument_immediate_mode_optional

            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['immediate_mode'] = self.context['immediate_mode']

        class RESTAPI(SourceBackendActionInterfaceRequestRESTAPI):
            class Argument:
                immediate_mode = argument_immediate_mode_optional

            def process_action_data(self):
                super().process_action_data()

                immediate_mode = self.action_kwargs.get(
                    'immediate_mode', DEFAULT_IMMEDIATE_MODE
                )

                if immediate_mode:
                    request = self.context['view'].request

                    serializer = DocumentSerializer(
                        context={'request': request},
                        instance=self.action_data
                    )

                    self.interface_result = Response(
                        data=serializer.data, status=status.HTTP_201_CREATED
                    )

            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['immediate_mode'] = self.context['immediate_mode']

        class Task(SourceBackendActionInterfaceTask):
            class Argument:
                immediate_mode = argument_immediate_mode_required

            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['immediate_mode'] = self.context['immediate_mode']

        class View(SourceBackendActionInterfaceRequestViewForm):
            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['immediate_mode'] = DEFAULT_IMMEDIATE_MODE

    def _background_task(self, immediate_mode, **kwargs):
        result = super()._background_task(**kwargs)

        if immediate_mode:
            server_upload_entry = result['server_upload_entry_list'][0]

            document_file_task_kwargs = self.get_document_file_task_kwargs(
                server_upload_entry=server_upload_entry, **kwargs
            )
            document_file_task_kwargs['is_document_upload_sequence'] = True

            document_file_task_kwargs['shared_uploaded_file_id'] = server_upload_entry[
                'shared_uploaded_file_id'
            ]

            task_document_file_create.apply_async(
                kwargs=document_file_task_kwargs
            )
        else:
            return result

    def _execute(self, immediate_mode, **kwargs):
        if immediate_mode:
            self.document = kwargs['document_type'].documents_create(
                description=kwargs['description'], label=kwargs['label'],
                language=kwargs['language'], user=kwargs['user']
            )

            super()._execute(immediate_mode=immediate_mode, **kwargs)

            return self.document
        else:
            super()._execute(immediate_mode=immediate_mode, **kwargs)

    def get_task_kwargs(self, immediate_mode, **kwargs):
        result = super().get_task_kwargs(**kwargs)

        result['action_interface_kwargs']['immediate_mode'] = immediate_mode

        document = getattr(self, 'document', None)

        if document:
            result['action_interface_kwargs']['document_id'] = document.pk

        return result
