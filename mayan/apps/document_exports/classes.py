from furl import furl

from django.apps import apps
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.converter.utils import object_list_export_to_pdf
from mayan.apps.locales.utils import to_language

from .events import event_document_version_exported
from .literals import (
    DEFAULT_DOCUMENT_VERSION_EXPORT_RESOLUTION,
    DOCUMENT_VERSION_EXPORT_MESSAGE_BODY,
    DOCUMENT_VERSION_EXPORT_MESSAGE_SUBJECT
)


class DocumentVersionExporter:
    def __init__(self, document_version):
        self.document_version = document_version

    def get_page_list(self):
        return [
            page for page in self.document_version.pages if page.content_object
        ]

    def export(self, file_object, resolution=None):
        if not resolution:
            resolution = DEFAULT_DOCUMENT_VERSION_EXPORT_RESOLUTION

        page_list = self.get_page_list()

        return object_list_export_to_pdf(
            file_object=file_object, object_list=page_list,
            resolution=resolution
        )

    def export_to_download_file(
        self, organization_installation_url='', user=None
    ):
        DownloadFile = apps.get_model(
            app_label='storage', model_name='DownloadFile'
        )
        Message = apps.get_model(
            app_label='messaging', model_name='Message'
        )

        download_file = DownloadFile.objects.create_from_content_function(
            content_function=self.export,
            filename='{}.pdf'.format(self.document_version),
            label=_(message='Document version export to PDF'), user=user
        )

        event_document_version_exported.commit(
            action_object=download_file, actor=user,
            target=self.document_version
        )

        if user:
            download_list_url = furl(organization_installation_url).join(
                reverse(
                    viewname='storage:download_file_list'
                )
            ).tostr()

            download_url = furl(organization_installation_url).join(
                reverse(
                    viewname='storage:download_file_download',
                    kwargs={'download_file_id': download_file.pk}
                )
            ).tostr()

            Message.objects.create(
                sender_object=download_file,
                user=user,
                subject=to_language(
                    language=user.locale_profile.language,
                    promise=DOCUMENT_VERSION_EXPORT_MESSAGE_SUBJECT
                ),
                body=to_language(
                    language=user.locale_profile.language,
                    promise=DOCUMENT_VERSION_EXPORT_MESSAGE_BODY
                ) % {
                    'download_list_url': download_list_url,
                    'download_url': download_url,
                    'document_version': self.document_version,
                }
            )
