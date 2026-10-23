import logging

import yaml

from django.core.exceptions import ValidationError
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.serialization import yaml_load
from mayan.apps.credentials.class_mixins import (
    BackendMixinCredentialsOptional
)
from mayan.apps.templating.template_backends import Template

from ..classes import SourceStoredFile

from .literals import (
    DEFAULT_STORAGE_BACKEND, DEFAULT_STORAGE_BACKEND_ARGUMENTS
)

logger = logging.getLogger(name=__name__)


class SourceBackendMixinStoredFileLocationStorageBackend(
    BackendMixinCredentialsOptional
):
    @classmethod
    def get_form_fields(cls):
        fields = super().get_form_fields()

        fields.update(
            {
                'storage_backend': {
                    'class': 'django.forms.CharField',
                    'default': DEFAULT_STORAGE_BACKEND,
                    'help_text': _(
                        message='Python path to the Storage subclass used to '
                        'access the source files.'
                    ),
                    'kwargs': {
                        'max_length': 255,
                    },
                    'label': _(message='Storage backend'),
                    'required': True
                },
                'storage_backend_arguments': {
                    'class': 'mayan.apps.templating.fields.TemplateField',
                    'default': DEFAULT_STORAGE_BACKEND_ARGUMENTS,
                    'kwargs': {
                        'initial_help_text': _(
                            message='Arguments to pass to the storage '
                            'backend. Use YAML format. The credential object '
                            'is available as {{ credential }}.'
                        ),
                        'max_length': 255,
                    },
                    'label': _(message='Storage backend arguments'),
                    'required': False
                }
            }
        )

        return fields

    @classmethod
    def get_form_fieldsets(cls):
        fieldsets = super().get_form_fieldsets()

        fieldsets += (
            (
                _(message='Storage'), {
                    'fields': (
                        'storage_backend', 'storage_backend_arguments'
                    )
                },
            ),
        )

        return fieldsets

    def get_storage_backend_arguments(self):
        field_value_arguments = self.kwargs.get(
            'storage_backend_arguments', '{}'
        )
        template_arguments = Template(template_string=field_value_arguments)
        context = {}

        credential = self.get_credential()
        if credential:
            context['credential'] = credential

        arguments = '{}'.format(
            template_arguments.render(context=context)
        )

        arguments = arguments.strip()

        try:
            return yaml_load(stream=arguments)
        except yaml.YAMLError:
            raise ValidationError(
                _(
                    message='Unable to initialize storage. Check the storage '
                    'backend arguments.'
                )
            )

    def get_storage_backend_class(self):
        try:
            return import_string(
                dotted_path=self.kwargs.get('storage_backend')
            )
        except Exception as exception:
            message = _(
                message='Unable to initialize storage. Check the storage '
                'backend dotted path.'
            )
            raise ValueError(message) from exception

    def get_storage_backend_instance(self):
        storage_backend_arguments = self.get_storage_backend_arguments()
        storage_backend_class = self.get_storage_backend_class()

        try:
            return storage_backend_class(**storage_backend_arguments)
        except Exception as exception:
            message = _(
                message='Unable to initialize storage; %s'
            ) % exception

            logger.fatal(message)
            raise TypeError(message) from exception

    def get_stored_file_list(self):
        regex_exclude = self.get_regex_exclude()
        regex_include = self.get_regex_include()

        storage_backend_instance = self.get_storage_backend_instance()

        try:
            folders, entries = storage_backend_instance.listdir('')

            for entry in entries:
                entry_name = str(entry)

                if regex_include.match(string=entry_name) and not regex_exclude.match(string=entry_name):
                    yield SourceStoredFile(filename=entry_name, source=self)
        except Exception as exception:
            message = 'Unable get list of files from source: {}; {}'.format(
                self, exception
            )

            logger.error(message)
            raise ValueError(message) from exception
