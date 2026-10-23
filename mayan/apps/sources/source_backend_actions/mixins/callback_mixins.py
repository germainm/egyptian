from django.apps import apps

from mayan.apps.common.utils import get_class_full_name


class SourceBackendActionMixinCallbackBase:
    def _assemble_callback(self, callback_name, result, task_kwargs):
        callback_kwargs_base = self.get_callback_kwargs()

        callback_kwargs = callback_kwargs_base.copy()

        self_get_callback_kwargs_method_name = 'get_callback_kwargs_{}'.format(callback_name)
        self_get_callback_kwargs_method = getattr(
            self, self_get_callback_kwargs_method_name
        )

        callback_kwargs.update(
            **self_get_callback_kwargs_method(task_kwargs=task_kwargs)
        )

        Source = apps.get_model(app_label='sources', model_name='Source')

        callback_info = {
            'dotted_path': get_class_full_name(klass=Source),
            'function_name': 'callback_{}'.format(callback_name),
            'kwargs': callback_kwargs
        }

        result.setdefault(
            'callback_dict', {}
        )
        callback_dict = result['callback_dict']
        callback_dict.setdefault(
            callback_name, callback_info
        )

    def get_callback_kwargs(self, **kwargs):
        return {
            'source_id': self.source.pk
        }

    def get_callback_kwargs_post_document_create(self, task_kwargs):
        return {}

    def get_callback_kwargs_post_document_file_create(self, task_kwargs):
        return {}

    def get_callback_kwargs_post_document_file_upload(self, task_kwargs):
        return {}


class SourceBackendActionMixinCallbackDocumentUploadBase:
    def get_document_task_kwargs(self, **kwargs):
        result = super().get_document_task_kwargs(**kwargs)

        self._assemble_callback(
            callback_name='post_document_create', result=result,
            task_kwargs=kwargs
        )
        self._assemble_callback(
            callback_name='post_document_file_create', result=result,
            task_kwargs=kwargs
        )
        self._assemble_callback(
            callback_name='post_document_file_upload', result=result,
            task_kwargs=kwargs
        )

        return result


class SourceBackendActionMixinCallbackDocumentFileUploadBase:
    def get_document_file_task_kwargs(self, **kwargs):
        result = super().get_document_task_kwargs(**kwargs)

        self._assemble_callback(
            callback_name='post_document_file_create', result=result,
            task_kwargs=kwargs
        )
        self._assemble_callback(
            callback_name='post_document_file_upload', result=result,
            task_kwargs=kwargs
        )
        return result


class SourceBackendActionMixinCallbackDocumentUpload(
    SourceBackendActionMixinCallbackDocumentUploadBase,
    SourceBackendActionMixinCallbackDocumentFileUploadBase,
    SourceBackendActionMixinCallbackBase
):
    pass


class SourceBackendActionMixinCallbackDocumentFileUpload(
    SourceBackendActionMixinCallbackDocumentFileUploadBase,
    SourceBackendActionMixinCallbackBase
):
    pass
