from django.core.files import File

from rest_framework import status
from rest_framework.response import Response

from mayan.apps.sources.source_backend_actions.interfaces import (
    SourceBackendActionInterface, SourceBackendActionInterfaceRequestRESTAPI,
    SourceBackendActionInterfaceRequestViewForm,
    SourceBackendActionInterfaceTask
)
from mayan.apps.storage.models import SharedUploadedFile

from .arguments import (
    argument_file, argument_file_object, argument_shared_uploaded_file_id
)


class SourceBackendActionMixinFileUser:
    accept_files = True

    class Interface:
        class Model(SourceBackendActionInterface):
            class Argument:
                file_object = argument_file_object

            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['file_object'] = File(
                    file=self.context['file_object']
                )

        class RESTAPI(SourceBackendActionInterfaceRequestRESTAPI):
            class Argument:
                file = argument_file

            def process_action_data(self):
                super().process_action_data()

                self.interface_result = Response(
                    status=status.HTTP_202_ACCEPTED
                )

            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['file_object'] = self.context['file']

        class Task(SourceBackendActionInterfaceTask):
            class Argument:
                shared_uploaded_file_id = argument_shared_uploaded_file_id

            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['shared_uploaded_file_id'] = self.context['shared_uploaded_file_id']

        class View(SourceBackendActionInterfaceRequestViewForm):
            def process_interface_context(self):
                super().process_interface_context()

                form_file = self.context['forms']['source_form'].cleaned_data['file']

                self.action_kwargs['file_object'] = form_file

    def _background_task(self, shared_uploaded_file_id, **kwargs):
        result = super()._background_task(**kwargs)

        result['server_upload_entry_list'] = (
            {'shared_uploaded_file_id': shared_uploaded_file_id},
        )

        return result

    def _execute(self, file_object, **kwargs):
        self.shared_uploaded_file = SharedUploadedFile.objects.create(
            file=file_object
        )

        super()._execute(**kwargs)

    def get_task_kwargs(self, **kwargs):
        result = super().get_task_kwargs(**kwargs)

        result['action_interface_kwargs']['shared_uploaded_file_id'] = self.shared_uploaded_file.pk

        return result
