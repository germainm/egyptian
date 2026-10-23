from django.core.exceptions import ImproperlyConfigured
from django.core.files import File
from django.http import StreamingHttpResponse
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response

from mayan.apps.converter.classes import ConverterBase
from mayan.apps.converter.utils import IndexedDictionary
from mayan.apps.sources.source_backend_actions.interfaces import (
    SourceBackendActionInterface, SourceBackendActionInterfaceRequestRESTAPI,
    SourceBackendActionInterfaceRequestView,
    SourceBackendActionInterfaceRequestViewForm,
    SourceBackendActionInterfaceTask
)
from mayan.apps.storage.models import SharedUploadedFile

from .arguments import (
    argument_encoded_filename, argument_file_cleanup,
    argument_file_identifier, argument_maximum_layer_order,
    argument_transformation_instance_list, argument_user
)


class SourceBackendActionMixinFileStoredDeleteBase:
    class Interface:
        class Model(SourceBackendActionInterface):
            class Argument:
                encoded_filename = argument_encoded_filename

            def process_interface_context(self):
                super().process_interface_context()
                self.action_kwargs['encoded_filename'] = self.context[
                    'encoded_filename'
                ]

    def _execute(self, encoded_filename, **kwargs):
        source_backend_instance = self.source.get_backend_instance()

        source_backend_instance.action_file_delete(
            encoded_filename=encoded_filename
        )


class SourceBackendActionMixinFileStoredDeleteInteractive(
    SourceBackendActionMixinFileStoredDeleteBase
):
    class Interface:
        class RESTAPI(SourceBackendActionInterfaceRequestRESTAPI):
            class Argument:
                encoded_filename = argument_encoded_filename

            def process_interface_context(self):
                super().process_interface_context()
                self.action_kwargs['encoded_filename'] = self.context[
                    'encoded_filename'
                ]

        class View(SourceBackendActionInterfaceRequestView):
            class Argument:
                encoded_filename = argument_encoded_filename

            def get_confirmation_context(self, encoded_filename, **kwargs):
                source_backend_instance = self.action.source.get_backend_instance()

                stored_file = source_backend_instance.get_stored_file(
                    encoded_filename=encoded_filename
                )

                context = {
                    'delete_view': True,
                    'object': stored_file,
                    'object_name': _(message='Stored file'),
                    'title': _(
                        message='Delete stored file "%s"?'
                    ) % stored_file,
                }

                return context

            def process_interface_context(self):
                super().process_interface_context()
                self.action_kwargs['encoded_filename'] = self.context[
                    'encoded_filename'
                ]

    def _execute(self, encoded_filename, **kwargs):
        source_backend_instance = self.source.get_backend_instance()

        source_backend_instance.action_file_delete(
            encoded_filename=encoded_filename
        )


class SourceBackendActionMixinFileStoredImage:
    class Interface:
        class Model(SourceBackendActionInterface):
            class Argument:
                encoded_filename = argument_encoded_filename
                maximum_layer_order = argument_maximum_layer_order
                transformation_instance_list = argument_transformation_instance_list
                user = argument_user

            def process_action_data(self):
                super().process_action_data()

                self.interface_result = self.action_data()

            def process_interface_context(self):
                super().process_interface_context()
                self.action_kwargs['encoded_filename'] = self.context['encoded_filename']
                self.action_kwargs['maximum_layer_order'] = self.context['maximum_layer_order']
                self.action_kwargs['transformation_instance_list'] = self.context['transformation_instance_list']
                self.action_kwargs['user'] = self.context['user']

        class RESTAPI(SourceBackendActionInterfaceRequestRESTAPI):
            class Argument:
                encoded_filename = argument_encoded_filename

            def process_action_data(self):
                super().process_action_data()

                content_type = ConverterBase.get_output_content_type()

                self.interface_result = StreamingHttpResponse(
                    content_type=content_type,
                    streaming_content=self.action_data()
                )

            def process_interface_context(self):
                super().process_interface_context()
                self.action_kwargs['encoded_filename'] = self.context['encoded_filename'][0]

                query_dict = self.context['request'].GET

                self.action_kwargs['transformation_instance_list'] = IndexedDictionary(
                    dictionary=query_dict
                ).as_instance_list()

                self.action_kwargs['maximum_layer_order'] = query_dict.get(
                    'maximum_layer_order'
                )
                self.action_kwargs['user'] = self.context['request'].user

    def _execute(
        self, encoded_filename, maximum_layer_order=None,
        transformation_instance_list=None, user=None
    ):
        source_backend_instance = self.source.get_backend_instance()

        return source_backend_instance.action_file_image(
            encoded_filename=encoded_filename,
            maximum_layer_order=maximum_layer_order,
            transformation_instance_list=transformation_instance_list,
            user=user
        )


class SourceBackendActionMixinFileStoredList:
    stored_file_list_method_name = 'action_file_list'

    class Interface:
        class Model(SourceBackendActionInterface):
            def process_action_data(self):
                super().process_action_data()

                self.interface_result = self.action_data

        class RESTAPI(SourceBackendActionInterfaceRequestRESTAPI):
            def process_action_data(self):
                self.action_data = list(self.action_data)
                super().process_action_data()

    def _execute(self):
        source_backend_instance = self.source.get_backend_instance()

        source_stored_file_get_method = getattr(
            source_backend_instance, self.stored_file_list_method_name
        )

        return source_stored_file_get_method()


class SourceBackendActionMixinFileStoredBase:
    default_file_cleanup = False
    stored_file_identifier_name = 'file_identifier'
    stored_method_name_file_cleanup = 'action_file_cleanup'
    stored_method_name_file_get = 'action_file_get'

    class Interface:
        class Task(SourceBackendActionInterfaceTask):
            class Argument:
                file_cleanup = argument_file_cleanup

            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['file_cleanup'] = self.context['file_cleanup']

    def _background_task(self, file_identifier, file_cleanup=None, **kwargs):
        result = super()._background_task(**kwargs)
        if file_identifier is None:
            result['server_upload_entry_list'] = ()
            return result

        source_backend_instance = self.source.get_backend_instance()

        kwargs = {
            self.stored_file_identifier_name: file_identifier
        }

        source_stored_file_get_method = getattr(
            source_backend_instance, self.stored_method_name_file_get
        )

        result['server_upload_entry_list'] = []

        server_upload_entry_generator = source_stored_file_get_method(
            **kwargs
        )

        if server_upload_entry_generator is None:
            raise ImproperlyConfigured(
                'Source backend method `{}` must return an iterator of at '
                'least one element.'.format(
                    self.stored_method_name_file_get
                )
            )

        while True:
            try:
                server_upload_entry = next(server_upload_entry_generator)

                result['server_upload_entry_list'].append(
                    self.process_server_upload_entry(
                        server_upload_entry=server_upload_entry
                    )
                )
            except StopIteration:
                """
                No more files to process.
                """
                break

        if file_cleanup is None:
            file_cleanup = self.default_file_cleanup

        if file_cleanup:
            source_stored_file_cleanup_method = getattr(
                source_backend_instance, self.stored_method_name_file_cleanup,
                None
            )

            if source_stored_file_cleanup_method:
                source_stored_file_cleanup_method(**kwargs)

        return result

    def get_task_kwargs(self, file_identifier, file_cleanup=None, **kwargs):
        result = super().get_task_kwargs(**kwargs)

        result['action_interface_kwargs'].update(
            {
                'file_cleanup': file_cleanup,
                'file_identifier': file_identifier
            }
        )

        return result

    def process_server_upload_entry(self, server_upload_entry):
        file_object = server_upload_entry.pop('file')

        with file_object.open(mode='rb') as file_object:
            shared_uploaded_file = SharedUploadedFile.objects.create(
                file=File(
                    file=file_object
                )
            )

            server_upload_entry['shared_uploaded_file_id'] = shared_uploaded_file.pk
            return server_upload_entry


class SourceBackendActionMixinFileStoredInteractive(
    SourceBackendActionMixinFileStoredBase
):
    class Interface:
        class Model(SourceBackendActionInterface):
            class Argument:
                file_identifier = argument_file_identifier

            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['file_identifier'] = self.context[
                    'file_identifier'
                ]

                source_backend_instance = self.action.source.get_backend_instance()

                self.action_kwargs['file_cleanup'] = source_backend_instance.kwargs.get(
                    'delete_after_upload', False
                )

        class RESTAPI(SourceBackendActionInterfaceRequestRESTAPI):
            def process_action_data(self):
                super().process_action_data()

                self.interface_result = Response(
                    status=status.HTTP_202_ACCEPTED
                )

            def process_interface_context(self):
                super().process_interface_context()
                self.action_kwargs['file_identifier'] = self.context[
                    self.action.stored_file_identifier_name
                ]

                source_backend_instance = self.action.source.get_backend_instance()

                self.action_kwargs['file_cleanup'] = source_backend_instance.kwargs.get(
                    'delete_after_upload', False
                )

        class Task(SourceBackendActionInterfaceTask):
            class Argument:
                file_identifier = argument_file_identifier

            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['file_identifier'] = self.context[
                    'file_identifier'
                ]

                source_backend_instance = self.action.source.get_backend_instance()

                self.action_kwargs['file_cleanup'] = source_backend_instance.kwargs.get(
                    'delete_after_upload', False
                )

        class View(SourceBackendActionInterfaceRequestViewForm):
            def process_interface_context(self):
                super().process_interface_context()

                form = self.context['forms']['source_form']

                stored_source_file_id = form.cleaned_data['stored_source_file_id']

                self.action_kwargs['file_identifier'] = stored_source_file_id

                source_backend_instance = self.action.source.get_backend_instance()

                self.action_kwargs['file_cleanup'] = source_backend_instance.kwargs.get(
                    'delete_after_upload', False
                )


class SourceBackendActionMixinFileStoredInteractiveNot(
    SourceBackendActionMixinFileStoredBase
):
    class Interface:
        class Model(SourceBackendActionInterface):
            def process_interface_context(self):
                super().process_interface_context()

                source_backend_instance = self.action.source.get_backend_instance()

                self.action_kwargs['file_identifier'] = source_backend_instance.get_file_identifier()

        class Task(SourceBackendActionInterfaceTask):
            class Argument:
                file_cleanup = argument_file_cleanup
                file_identifier = argument_file_identifier

            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['file_cleanup'] = self.context['file_cleanup']
                self.action_kwargs['file_identifier'] = self.context['file_identifier']

    def convert_dry_run_to_file_cleanup(self, dry_run):
        if dry_run is True:
            return False
        elif dry_run is False:
            return True
        elif dry_run is None:
            return True

    def get_task_kwargs(self, dry_run, **kwargs):
        result = super().get_task_kwargs(**kwargs)

        result['action_interface_kwargs']['file_cleanup'] = self.convert_dry_run_to_file_cleanup(
            dry_run=dry_run
        )

        return result
