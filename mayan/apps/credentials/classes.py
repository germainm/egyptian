from django.utils.translation import gettext_lazy as _

from mayan.apps.backends.classes import DynamicFormModelBackend

from .events import event_credential_used


class CredentialBackend(DynamicFormModelBackend):
    _backend_app_label = 'credentials'
    _backend_model_name = 'StoredCredential'
    _loader_module_name = 'credential_backends'

    form_fieldsets = (
        (
            _(message='General'), {
                'fields': ('label', 'internal_name')
            }
        ),
    )

    def get_credential(self, action_object=None, user=None):
        model_instance = self.get_model_instance()

        backend_data = model_instance.get_backend_data()
        event_credential_used.commit(
            action_object=action_object, actor=user, target=model_instance
        )
        return backend_data


class CredentialBackendNull(CredentialBackend):
    label = _(message='Null backend')
