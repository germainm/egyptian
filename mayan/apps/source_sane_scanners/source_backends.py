import logging

import sh

from django.core.files import File
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.serialization import yaml_load
from mayan.apps.source_generated_files.source_backend_actions.generated_file_actions import (
    SourceBackendActionGenerateFileDocumentFileUpload,
    SourceBackendActionGenerateFileDocumentUpload
)
from mayan.apps.source_interactive.source_backends.mixins import (
    SourceBackendMixinInteractive
)
from mayan.apps.sources.source_backends.base import SourceBackend
from mayan.apps.storage.utils import NamedTemporaryFile, touch

from .literals import DEFAULT_SCANIMAGE_TIMEOUT
from .utils import get_command_path_scanimage

logger = logging.getLogger(name=__name__)


class SourceBackendSANEScanner(SourceBackendMixinInteractive, SourceBackend):
    action_class_list = (
        SourceBackendActionGenerateFileDocumentFileUpload,
        SourceBackendActionGenerateFileDocumentUpload
    )
    label = _(message='SANE Scanner')
    widgets = {
        'arguments': {
            'class': 'django.forms.widgets.Textarea', 'kwargs': {
                'attrs': {
                    'rows': 10
                }
            }
        }
    }

    @classmethod
    def get_form_fields(cls):
        fields = super().get_form_fields()
        fields.update(
            {
                'device_name': {
                    'class': 'django.forms.CharField',
                    'help_text': _(
                        message='Device name as returned by the SANE backend.'
                    ),
                    'kwargs': {'max_length': 255},
                    'label': _(message='Device name'),
                    'required': True
                },
                'arguments': {
                    'class': 'django.forms.CharField',
                    'help_text': _(
                        message='YAML formatted arguments to pass to the '
                        '`scanimage` command. The arguments will change '
                        'depending on the device. Execute `scanimage --help '
                        '--device-name=DEVICE` for the list of supported '
                        'arguments.'
                    ),
                    'label': _(message='Arguments'),
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
                _(message='SANE client'), {
                    'fields': ('device_name', 'arguments')
                },
            ),
        )

        return fieldsets

    def action_file_get(self, file_identifier):
        with NamedTemporaryFile() as file_object:
            try:
                self.call_command_scanimage(_out=file_object.name)
            except sh.ErrorReturnCode:
                touch(filename=file_object.name)
                raise
            else:
                file_object.seek(0)

                filename = 'scan {}'.format(
                    now()
                )
                yield {
                    'file': File(file=file_object, name=filename)
                }

    def call_command_scanimage(self, **kwargs):
        command_scanimage = self.get_command_scanimage()

        command_arguments = self.get_command_arguments(**kwargs)

        command_scanimage(**command_arguments)

    def get_command_arguments(self, **kwargs):
        loaded_arguments = yaml_load(
            stream=self.kwargs.get('arguments', '{}')
        ) or {}

        loaded_arguments.update(**kwargs)

        loaded_arguments.setdefault('_timeout', DEFAULT_SCANIMAGE_TIMEOUT)

        return loaded_arguments

    def get_command_scanimage(self):
        command_path = get_command_path_scanimage(
            dotted_name=self.backend_class_path
        )

        command_scanimage = sh.Command(path=command_path)

        return command_scanimage.bake(
            device_name=self.kwargs['device_name'], format='tiff'
        )

    def get_view_context(self, context, request):
        return {
            'subtemplates_list': [
                {
                    'context': {
                        'forms': context['forms'],
                        'is_multipart': True,
                        'title': _(message='Document properties'),
                        'submit_label': _(message='Scan')
                    },
                    'name': 'appearance/partials/form/multiple.html'
                }
            ]
        }
