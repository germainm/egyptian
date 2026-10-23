from django.utils.translation import gettext_lazy as _

from mayan.apps.credentials.classes import CredentialBackend


class CredentialBackendGoogleServiceAccount(CredentialBackend):
    form_field_order = (
        'project_id', 'private_key_id', 'private_key', 'client_email',
        'client_id', 'auth_uri', 'token_uri', 'auth_provider_x509_cert_url',
        'client_x509_cert_url'
    )
    form_field_widgets = {
        'private_key': {
            'class': 'django.forms.widgets.Textarea'
        }
    }
    form_fields = {
        'project_id': {
            'label': _(message='Project ID'),
            'class': 'django.forms.CharField', 'default': '',
            'kwargs': {
                'max_length': 254
            }, 'required': True
        },
        'private_key_id': {
            'label': _(message='Private Key ID'),
            'class': 'django.forms.CharField', 'default': '',
            'kwargs': {
                'max_length': 254
            }, 'required': True
        },
        'private_key': {
            'label': _(message='Private Key'),
            'class': 'django.forms.CharField', 'default': ''
        },
        'client_email': {
            'label': _(message='Client email'),
            'class': 'django.forms.CharField', 'default': '',
            'kwargs': {
                'max_length': 254
            }, 'required': True
        },
        'client_id': {
            'label': _(message='Client ID'),
            'class': 'django.forms.CharField', 'default': '',
            'kwargs': {
                'max_length': 254
            }, 'required': True
        },
        'auth_uri': {
            'label': _(message='Authentication URI'),
            'class': 'django.forms.CharField',
            'default': 'https://accounts.google.com/o/oauth2/auth',
            'kwargs': {
                'max_length': 254
            }, 'required': True
        },
        'token_uri': {
            'label': _(message='Token URI'),
            'class': 'django.forms.CharField',
            'default': 'https://oauth2.googleapis.com/token',
            'kwargs': {
                'max_length': 254
            }, 'required': True
        },
        'auth_provider_x509_cert_url': {
            'label': _(message='X509 certificate provider URL'),
            'class': 'django.forms.CharField',
            'default': 'https://www.googleapis.com/oauth2/v1/certs',
            'kwargs': {
                'max_length': 254
            }, 'required': True
        },
        'client_x509_cert_url': {
            'label': _(message='Client X509 certificate URL'),
            'class': 'django.forms.CharField', 'default': '',
            'kwargs': {
                'max_length': 254
            }, 'required': True
        }
    }
    label = _(message='Google Service Account')

    @classmethod
    def get_form_fieldsets(cls):
        fieldsets = super().get_form_fieldsets()

        fieldsets += (
            (
                _(message='Project'), {
                    'fields': ('project_id',)
                }
            ),
            (
                _(message='Secrets'), {
                    'fields': ('private_key_id', 'private_key', 'token_uri')
                }
            ),
            (
                _(message='Identity'), {
                    'fields': ('client_email', 'client_id', 'auth_uri')
                }
            ),
            (
                _(message='Certificate'), {
                    'fields': (
                        'auth_provider_x509_cert_url', 'client_x509_cert_url'
                    )
                }
            )
        )

        return fieldsets

    @classmethod
    def post_processing(cls, obj):
        for key, value in obj.items():
            obj[key] = value.replace('\\n', '\n')

        return obj
