import email
import logging
import random

from django.core.files.base import ContentFile
from django.utils.encoding import force_bytes
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.utils import convert_to_internal_name
from mayan.apps.credentials.class_mixins import BackendMixinCredentials
from mayan.apps.source_periodic.source_backends.mixins import (
    SourceBackendMixinPeriodicCompressed
)

from ..source_backend_actions import SourceBackendActionEmailDocumentUpload

logger = logging.getLogger(name=__name__)


class SourceBackendMixinEmail(
    BackendMixinCredentials, SourceBackendMixinPeriodicCompressed
):
    action_class_list = (SourceBackendActionEmailDocumentUpload,)

    @classmethod
    def get_form_fields(cls):
        fields = super().get_form_fields()

        fields.update(
            {
                'host': {
                    'class': 'django.forms.CharField',
                    'label': _(message='Host'),
                    'kwargs': {
                        'max_length': 128
                    },
                    'required': True
                },
                'ssl': {
                    'class': 'django.forms.BooleanField',
                    'default': True,
                    'label': _(message='SSL'),
                    'required': False
                },
                'port': {
                    'class': 'django.forms.IntegerField',
                    'help_text': _(
                        message='Typical choices are 110 for POP3, 995 for '
                        'POP3 over SSL, 143 for IMAP, 993 for IMAP over SSL.'
                    ),
                    'kwargs': {
                        'min_value': 0
                    },
                    'label': _(message='Port')
                },
                'store_body': {
                    'class': 'django.forms.BooleanField',
                    'default': True,
                    'help_text': _(
                        message='Store the body of the email as a text '
                        'document.'
                    ),
                    'label': _(message='Store email body'),
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
                _(message='Common email options'), {
                    'fields': (
                        'host', 'ssl', 'port', 'store_body'
                    )
                },
            ),
        )

        return fieldsets

    def process_message(self, message):
        bytes_message = force_bytes(s=message)

        message = email.message_from_bytes(
            policy=email.policy.default, s=bytes_message
        )

        return self._process_message_content(message=message)

    def _process_message_content(self, message, source_metadata=None):
        counter = 1
        if source_metadata is None:
            _source_metadata = {}
        else:
            _source_metadata = source_metadata.copy()

        for key, value in message.items():
            internal_name = convert_to_internal_name(value=key)
            _source_metadata[
                'email_{}'.format(internal_name)
            ] = value

        if message.is_multipart():
            for part in message.iter_parts():
                yield from self._process_message_content(
                    message=part, source_metadata=_source_metadata
                )
        else:
            if message.is_attachment() or message.get_content_disposition() == 'inline':
                content = message.get_content()
                if len(content) != 0:
                    detected_filename = message.get_filename()
                    if detected_filename:
                        label = detected_filename
                    else:
                        label = 'attachment-{}'.format(counter)
                        counter += 1

                    yield {
                        'file': ContentFile(
                            content=content, name=label,
                        ), 'source_metadata': _source_metadata
                    }
            else:
                if message.get_content_type() == 'text/html':
                    label = 'email_body.html'
                else:
                    label = 'email_body.txt'

                if self.kwargs['store_body']:
                    content = message.get_content()
                    bytes_content = force_bytes(s=content)
                    yield {
                        'file': ContentFile(
                            content=bytes_content, name=label
                        ), 'source_metadata': _source_metadata
                    }

    def get_file_identifier(self):
        file_list_generator = self.get_stored_file_list()

        file_list_generator = list(file_list_generator)

        if file_list_generator:
            return random.choice(seq=file_list_generator)
