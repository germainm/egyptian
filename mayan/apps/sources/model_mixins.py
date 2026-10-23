import logging

from django.apps import apps

from mayan.apps.converter.layers import layer_saved_transformations

logger = logging.getLogger(name=__name__)


class SourceBusinessLogicMixin:
    @staticmethod
    def callback_post_document_create(document, **kwargs):
        Source = apps.get_model(app_label='sources', model_name='Source')

        source = Source.objects.get(
            pk=kwargs['source_id']
        )

        source_backend_instance = source.get_backend_instance()

        source_backend_instance.callback_post_document_create(
            document=document, **kwargs
        )

    @staticmethod
    def callback_post_document_file_create(document_file, **kwargs):
        Source = apps.get_model(app_label='sources', model_name='Source')

        source = Source.objects.get(
            pk=kwargs['source_id']
        )

        source_backend_instance = source.get_backend_instance()

        source_backend_instance.callback_post_document_file_create(
            document_file=document_file, **kwargs
        )

    @staticmethod
    def callback_post_document_file_upload(document_file, **kwargs):
        Source = apps.get_model(app_label='sources', model_name='Source')

        source = Source.objects.get(
            pk=kwargs['source_id']
        )

        layer_saved_transformations.copy_transformations(
            source=source, targets=document_file.pages.all()
        )

        source_backend_instance = source.get_backend_instance()

        source_backend_instance.callback_post_document_file_upload(
            document_file=document_file, **kwargs
        )

    def action_execute(
        self, name, interface_name, interface_load_kwargs=None,
        interface_retrieve_kwargs=None
    ):
        action = self.get_action(name=name)

        return action.execute(
            interface_name=interface_name,
            interface_load_kwargs=interface_load_kwargs,
            interface_retrieve_kwargs=interface_retrieve_kwargs
        )

    @property
    def actions(self):
        return self.get_action_list()

    def fullname(self):
        return '{} {}'.format(
            self.get_backend_class_label(), self.label
        )

    def get_action(self, name):
        backend_instance = self.get_backend_instance()
        return backend_instance.get_action(name=name)

    def get_action_list(self):
        backend_instance = self.get_backend_instance()
        return backend_instance.get_action_list()
