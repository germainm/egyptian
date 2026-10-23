from mayan.apps.sources.source_backend_actions.interfaces import (
    SourceBackendActionInterface, SourceBackendActionInterfaceRequestRESTAPI,
    SourceBackendActionInterfaceRequestView, SourceBackendActionInterfaceTask
)
from mayan.apps.sources.source_backend_actions.mixins.callback_mixins import (
    SourceBackendActionMixinCallbackDocumentFileUpload,
    SourceBackendActionMixinCallbackDocumentUpload
)

from .arguments import argument_query_string


class SourceBackendActionMixinCallbackPostDocumentCreateUserInteractive:
    def get_callback_kwargs_post_document_create(self, task_kwargs):
        result = super().get_callback_kwargs_post_document_create(
            task_kwargs=task_kwargs
        )

        if 'user' in task_kwargs:
            result['user_id'] = task_kwargs['user'].pk

        return result


class SourceBackendActionMixinCallbackPostDocumentFileUploadUserInteractive:
    def get_callback_kwargs_post_document_file_upload(self, task_kwargs):
        result = super().get_callback_kwargs_post_document_file_upload(
            task_kwargs=task_kwargs
        )

        if 'user' in task_kwargs:
            result['user_id'] = task_kwargs['user'].pk

        return result


class SourceBackendActionMixinCallbackPostDocumentUploadQueryStringInteractive:
    class Interface:
        class Model(SourceBackendActionInterface):
            class Argument:
                query_string = argument_query_string

            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['query_string'] = self.context['query_string']

        class RESTAPI(SourceBackendActionInterfaceRequestRESTAPI):
            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['query_string'] = ''

        class Task(SourceBackendActionInterfaceTask):
            class Argument:
                query_string = argument_query_string

            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['query_string'] = self.context['query_string']

        class View(SourceBackendActionInterfaceRequestView):
            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['query_string'] = self.action.get_query_string(
                    request=self.context['request']
                )

    def get_callback_kwargs_post_document_create(self, task_kwargs):
        result = super().get_callback_kwargs_post_document_create(
            task_kwargs=task_kwargs
        )

        result['query_string'] = task_kwargs['query_string']

        return result

    def get_query_string(self, request):
        query_string = ''

        query_dict = request.GET.copy()
        query_dict.update(request.POST)

        if hasattr(query_dict, 'urlencode'):
            query_string = query_dict.urlencode()

        return query_string

    def get_task_kwargs(self, query_string, **kwargs):
        result = super().get_task_kwargs(**kwargs)

        result['action_interface_kwargs']['query_string'] = query_string

        return result


class SourceBackendActionMixinCallbackDocumentUploadInteractive(
    SourceBackendActionMixinCallbackPostDocumentFileUploadUserInteractive,
    SourceBackendActionMixinCallbackPostDocumentUploadQueryStringInteractive,
    SourceBackendActionMixinCallbackPostDocumentCreateUserInteractive,
    SourceBackendActionMixinCallbackDocumentUpload
):
    pass


class SourceBackendActionMixinCallbackDocumentFileUploadInteractive(
    SourceBackendActionMixinCallbackPostDocumentFileUploadUserInteractive,
    SourceBackendActionMixinCallbackDocumentFileUpload
):
    pass
