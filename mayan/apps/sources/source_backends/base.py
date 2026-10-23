from django.utils.translation import gettext_lazy as _

from mayan.apps.backends.class_mixins import DynamicFormBackendMixin
from mayan.apps.backends.classes import ModelBaseBackend

from ..exceptions import SourceActionExceptionUnknown

from .mixins import SourceBackendMixinSourceMetadata


class SourceBackendBase:
    action_class_list = None

    def callback_post_document_create(self, document, **kwargs):
        return

    def callback_post_document_file_create(self, document_file, **kwargs):
        return

    def callback_post_document_file_upload(self, document_file, **kwargs):
        return

    def clean(self):
        pass

    def create(self):
        pass

    def delete(self):
        pass

    def get_action(self, name):
        for entry in self.get_action_list():
            if entry.name == name:
                return entry

        raise SourceActionExceptionUnknown(
            'Unknown action `{}` for source `{}`.'.format(
                name, self.label
            )
        )

    def get_action_class_list(self):
        return self.action_class_list or ()

    def get_action_list(self):
        action_class_list = self.get_action_class_list() or ()

        source = self.get_model_instance()

        for action_class in action_class_list:
            yield action_class(source=source)

    def update(self):
        pass


class SourceBackend(
    DynamicFormBackendMixin, ModelBaseBackend,
    SourceBackendMixinSourceMetadata, SourceBackendBase
):
    _backend_app_label = 'sources'
    _backend_model_name = 'Source'
    _loader_module_name = 'source_backends'

    @classmethod
    def get_form_fieldsets(cls):
        fieldsets = (
            (
                _(message='General'), {
                    'fields': ('label', 'enabled')
                }
            ),
        )

        return fieldsets

    @classmethod
    def initialize(cls):
        pass

    @classmethod
    def post_load_modules(cls):
        for source_backend in cls.get_all():
            source_backend.initialize()

    def get_allow_action_execute(self, action, action_execute_kwargs=None):
        return self.get_model_instance().enabled

    def get_upload_form_class(self, action):
        from ..forms import UploadBaseForm

        return getattr(self, 'upload_form_class', UploadBaseForm)


class SourceBackendNull(SourceBackend):
    is_visible = False
    label = _(message='Null backend')
