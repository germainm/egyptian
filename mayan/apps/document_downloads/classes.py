import shutil
from zipfile import ZipFile

from furl import furl

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

from mayan.apps.locales.utils import to_language
from mayan.apps.templating.template_backends import Template


class DocumentFileCompressor:
    context_key_list = (
        'document_list', 'download_file', 'download_list_url', 'download_url'
    )

    def __init__(self, queryset):
        self.queryset = queryset

    def compress(self, file_object, _event_action_object=None, _event_actor=None):
        with ZipFile(file=file_object, mode='w') as archive:
            for document_file in self.queryset.all():
                document_file._event_action_object = _event_action_object
                document_file._event_actor = _event_actor
                with document_file.open(mode='rb', raw=True) as entry_file_object:
                    archive_name = str(document_file)
                    with archive.open(name=archive_name, mode='w') as archive_member_file_object:
                        shutil.copyfileobj(
                            fsrc=entry_file_object,
                            fdst=archive_member_file_object
                        )

    def compress_to_download_file(
        self, organization_installation_url='', filename=None, user=None
    ):
        from .settings import (
            setting_message_body_template, setting_message_subject_template
        )

        DownloadFile = apps.get_model(
            app_label='storage', model_name='DownloadFile'
        )
        Message = apps.get_model(
            app_label='messaging', model_name='Message'
        )

        if self.queryset.count():
            filename = filename or _(message='Document_file_bundle.zip')

            download_file = DownloadFile(
                filename=filename, label=_(
                    message='Compressed document files'
                ), user=user
            )
            download_file._event_actor = user
            download_file.save()

            with download_file.open(mode='wb+') as file_object:
                self.compress(
                    _event_action_object=download_file,
                    _event_actor=user, file_object=file_object
                )

            if user:
                download_list_url = furl(organization_installation_url).join(
                    reverse(viewname='storage:download_file_list')
                ).tostr()

                download_url = furl(organization_installation_url).join(
                    reverse(
                        kwargs={'download_file_id': download_file.pk},
                        viewname='storage:download_file_download'
                    )
                ).tostr()

                context_dictionary = {
                    'document_list': self.queryset,
                    'download_file': download_file,
                    'download_list_url': download_list_url,
                    'download_url': download_url
                }

                if set(context_dictionary.keys()) != set(DocumentFileCompressor.context_key_list):
                    raise ImproperlyConfigured(
                        'The expected and the actual message template '
                        'context keys do not match. Update the expected key '
                        'list to match the actual key list being passed '
                        'to the template.'
                    )

                body_message = _(
                    message=setting_message_body_template.value
                )

                message_body_template = Template(
                    template_string=to_language(
                        language=user.locale_profile.language,
                        promise=body_message
                    )
                )
                message_body_content = message_body_template.render(
                    context=context_dictionary
                )

                subject_message = _(
                    message=setting_message_subject_template.value
                )

                message_subject_template = Template(
                    template_string=to_language(
                        language=user.locale_profile.language,
                        promise=subject_message
                    )
                )
                message_subject_text = strip_tags(
                    message_subject_template.render(
                        context=context_dictionary
                    )
                )

                Message.objects.create(
                    body=message_body_content, sender_object=download_file,
                    subject=message_subject_text, user=user
                )
