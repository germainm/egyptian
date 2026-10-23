from django.utils.translation import gettext_lazy as _

from mayan.apps.backends.class_mixins import DynamicFormBackendMixin
from mayan.apps.backends.classes import ModelBaseBackend
from mayan.apps.credentials.class_mixins import BackendMixinCredentials


class MailerBackend(DynamicFormBackendMixin, ModelBaseBackend):
    _backend_app_label = 'mailer'
    _backend_model_name = 'UserMailer'
    _loader_module_name = 'mailers'
    class_path = ''

    @classmethod
    def get_form_fieldsets(cls):
        fieldsets = (
            (
                _(message='General'), {
                    'fields': ('label', 'enabled', 'default')
                }
            ),
        )

        return fieldsets

    def get_connection_kwargs(self):
        result = {}

        return result


class MailerBackendBaseEmail(MailerBackend):
    class_path = None
    form_fields = {
        'from': {
            'label': _(message='From'),
            'class': 'django.forms.CharField', 'default': '',
            'help_text': _(
                message='The sender\'s address. Some system will refuse '
                'to send messages if this value is not set.'
            ), 'kwargs': {
                'max_length': 48
            }, 'required': False
        }
    }
    label = None

    @classmethod
    def get_form_fieldsets(cls):
        fieldsets = super().get_form_fieldsets()

        fieldsets += (
            (
                _(message='Compatibility'), {
                    'fields': ('from',)
                }
            ),
        )

        return fieldsets

    def get_connection_kwargs(self):
        result = super().get_connection_kwargs()

        result['from'] = self.kwargs.get('from')

        return result


class MailerBackendCredentials(
    BackendMixinCredentials, MailerBackendBaseEmail
):
    label = _(message='Null backend')

    def get_connection_kwargs(self):
        result = super().get_connection_kwargs()

        model_instance = self.get_model_instance()
        credential = self.get_credential(action_object=model_instance)
        password = credential.get('password')
        username = credential['username']

        result.update(
            {'password': password, 'username': username}
        )

        return result


class MailerBackendNull(MailerBackend):
    label = _(message='Null backend')
