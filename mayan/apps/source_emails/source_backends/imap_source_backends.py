from contextlib import contextmanager
import imaplib
import logging

from django.utils.encoding import force_bytes, force_str
from django.utils.translation import gettext_lazy as _

from mayan.apps.sources.exceptions import SourceException
from mayan.apps.sources.source_backends.base import SourceBackend

from .literals import (
    DEFAULT_EMAIL_IMAP_MAILBOX, DEFAULT_EMAIL_IMAP_SEARCH_CRITERIA,
    DEFAULT_EMAIL_IMAP_STORE_COMMANDS
)
from .mixins import SourceBackendMixinEmail

logger = logging.getLogger(name=__name__)


class SourceBackendIMAPEmail(SourceBackendMixinEmail, SourceBackend):
    label = _(message='IMAP email')

    @classmethod
    def get_form_field_widgets(cls):
        widgets = super().get_form_field_widgets()

        widgets.update(
            {
                'search_criteria': {
                    'class': 'django.forms.widgets.Textarea'
                },
                'store_commands': {
                    'class': 'django.forms.widgets.Textarea'
                }
            }
        )

        return widgets

    @classmethod
    def get_form_fields(cls):
        fields = super().get_form_fields()

        fields.update(
            {
                'mailbox': {
                    'class': 'django.forms.fields.CharField',
                    'default': DEFAULT_EMAIL_IMAP_MAILBOX,
                    'help_text': _(
                        message='IMAP Mailbox from which to check for messages.'
                    ),
                    'kwargs': {
                        'max_length': 64,
                    },
                    'label': _(message='Mailbox')
                },
                'search_criteria': {
                    'blank': True,
                    'class': 'django.forms.fields.CharField',
                    'default': DEFAULT_EMAIL_IMAP_SEARCH_CRITERIA,
                    'help_text': _(
                        message='Criteria to use when searching for messages to '
                        'process. Use the format specified in '
                        'https://tools.ietf.org/html/rfc2060.html#section-6.4.4'
                    ),
                    'label': _(message='Search criteria'),
                    'null': True,
                },
                'store_commands': {
                    'blank': True,
                    'class': 'django.forms.fields.CharField',
                    'default': DEFAULT_EMAIL_IMAP_STORE_COMMANDS,
                    'help_text': _(
                        message='IMAP STORE command to execute on messages after '
                        'they are processed. One command per line. Use '
                        'the commands specified in '
                        'https://tools.ietf.org/html/rfc2060.html#section-6.4.6 '
                        'or the custom commands for your IMAP server.'
                    ),
                    'label': _(message='Store commands'),
                    'null': True, 'required': False
                },
                'execute_expunge': {
                    'class': 'django.forms.fields.BooleanField',
                    'default': True,
                    'help_text': _(
                        message='Execute the IMAP expunge command after processing '
                        'each email message.'
                    ),
                    'label': _(message='Execute expunge'),
                    'required': False
                },
                'mailbox_destination': {
                    'blank': True,
                    'class': 'django.forms.fields.CharField',
                    'help_text': _(
                        message='IMAP Mailbox to which processed messages will '
                        'be copied.'
                    ),
                    'label': _(message='Destination mailbox'),
                    'max_length': 96,
                    'null': True,
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
                _(message='IMAP protocol'), {
                    'fields': (
                        'mailbox', 'search_criteria', 'store_commands',
                        'execute_expunge', 'mailbox_destination'
                    )
                }
            ),
        )

        return fieldsets

    @contextmanager
    def _get_server(self):
        logger.debug(msg='Starting IMAP email connection')
        logger.debug(
            'host: %s', self.kwargs['host']
        )
        logger.debug(
            'ssl: %s', self.kwargs['ssl']
        )

        if self.kwargs['ssl']:
            imap_module_name = 'IMAP4_SSL'
        else:
            imap_module_name = 'IMAP4'

        imap_module = getattr(imaplib, imap_module_name)

        kwargs = {
            'host': self.kwargs['host'], 'port': self.kwargs['port']
        }

        model_instance = self.get_model_instance()
        credential = self.get_credential(action_object=model_instance)
        password = credential.get('password')
        username = credential.get('username')

        with imap_module(**kwargs) as server:
            server.login(password=password, user=username)

            try:
                server.select(
                    mailbox=self.kwargs['mailbox']
                )
            except Exception as exception:
                raise SourceException(
                    'Error selecting mailbox: {}; {}'.format(
                        self.kwargs['mailbox'], exception
                    )
                )
            else:
                yield server

    def action_file_delete(self, message_id):
        with self._get_server() as server:
            if self.kwargs['mailbox_destination']:
                try:
                    server.uid(
                        'COPY', message_id, self.kwargs['mailbox_destination']
                    )
                except Exception as exception:
                    raise SourceException(
                        'Error copying message uid {} to mailbox {}; '
                        '{}'.format(
                            message_id, self.kwargs['mailbox_destination'], exception
                        )
                    )

            if self.kwargs['store_commands']:
                for command in self.kwargs['store_commands'].split('\n'):
                    try:
                        args = [message_id]
                        args.extend(
                            command.strip().split(' ')
                        )
                        server.uid('STORE', *args)
                    except Exception as exception:
                        raise SourceException(
                            'Error executing IMAP store command "{}" '
                            'on message uid {}; {}'.format(
                                command, message_id, exception
                            )
                        )

            if self.kwargs['execute_expunge']:
                server.expunge()

    def action_file_get(self, message_id):
        message_id = force_bytes(s=message_id)

        with self._get_server() as server:
            status, data = server.uid('FETCH', message_id, '(RFC822)')

            try:
                yield from self.process_message(
                    message=data[0][1]
                )
            except Exception as exception:
                raise SourceException(
                    'Error processing message uid: {}; {}'.format(
                        message_id, exception
                    )
                )

    def get_stored_file_list(self):
        with self._get_server() as server:
            try:
                search_criteria = self.kwargs['search_criteria'].strip().split()

                status, data = server.uid(
                    'SEARCH', None, *search_criteria
                )
            except Exception as exception:
                raise SourceException(
                    'Error executing search command; {}'.format(exception)
                )
            else:
                if data:
                    uids = data[0].split()

                    logger.debug(
                        'messages count: %s', len(uids)
                    )
                    logger.debug('message uids: %s', uids)

                    for uid in uids:
                        logger.debug('message uid: %s', uid)

                        yield force_str(s=uid)
