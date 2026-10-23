from django.contrib.auth import get_user_model

from ..interfaces import (
    SourceBackendActionInterface, SourceBackendActionInterfaceRequestRESTAPI,
    SourceBackendActionInterfaceRequestView, SourceBackendActionInterfaceTask
)

from .arguments import argument_user, argument_user_id


class SourceBackendActionMixinUserBase:
    class Interface:
        class Model(SourceBackendActionInterface):
            class Argument:
                user = argument_user

            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['user'] = self.context['user']

        class Task(SourceBackendActionInterfaceTask):
            class Argument:
                user_id = argument_user_id

            def process_interface_context(self):
                super().process_interface_context()

                User = get_user_model()

                user_id = self.context.get('user_id')

                if user_id:
                    self.action_kwargs['user'] = User.objects.get(pk=user_id)

    def _extract_user_arguments(self, kwargs):
        user_arguments = {}
        user_arguments['user'] = kwargs.get('user')
        return user_arguments

    def _inject_user_information(self, user_arguments, result, **kwargs):
        user = user_arguments['user']

        if user:
            result['user_id'] = user.pk

    def get_document_file_task_kwargs(self, **kwargs):
        user_arguments = self._extract_user_arguments(kwargs=kwargs)

        result = super().get_document_file_task_kwargs(**kwargs)

        self._inject_user_information(
            user_arguments=user_arguments, result=result, **kwargs
        )
        return result

    def get_document_task_kwargs(self, **kwargs):
        user_arguments = self._extract_user_arguments(kwargs=kwargs)

        result = super().get_document_task_kwargs(**kwargs)

        self._inject_user_information(
            user_arguments=user_arguments, result=result, **kwargs
        )

        return result

    def get_task_kwargs(self, user=None, **kwargs):
        result = super().get_task_kwargs(**kwargs)

        if user:
            result['action_interface_kwargs']['user_id'] = user.pk

        return result


class SourceBackendActionMixinUserInteractive(
    SourceBackendActionMixinUserBase
):
    class Interface:
        class RESTAPI(SourceBackendActionInterfaceRequestRESTAPI):
            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['user'] = self.context['request'].user

        class View(SourceBackendActionInterfaceRequestView):
            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['user'] = self.context['request'].user


class SourceBackendActionMixinUserInteractiveNot(
    SourceBackendActionMixinUserBase
):
    pass
