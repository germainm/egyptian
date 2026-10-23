from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .classes import DocumentFileCompressor
from .literals import (
    DEFAULT_DOCUMENT_FILE_DOWNLOAD_BACKEND,
    DEFAULT_DOCUMENT_FILE_DOWNLOAD_BACKEND_ARGUMENTS,
    DEFAULT_DOCUMENT_FILE_DOWNLOAD_MESSAGE_BODY,
    DEFAULT_DOCUMENT_FILE_DOWNLOAD_MESSAGE_SUBJECT
)

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='Document downloads'), name='document_downloads'
)

setting_document_file_download_backend = setting_namespace.do_setting_add(
    default=DEFAULT_DOCUMENT_FILE_DOWNLOAD_BACKEND,
    global_name='DOCUMENT_DOWNLOADS_DOCUMENT_FILE_DOWNLOAD_BACKEND',
    help_text=_(
        'Path to the download subclass to use when downloading document '
        'files.'
    )
)
setting_document_file_download_backend_arguments = setting_namespace.do_setting_add(
    default=DEFAULT_DOCUMENT_FILE_DOWNLOAD_BACKEND_ARGUMENTS,
    global_name='DOCUMENT_DOWNLOADS_DOCUMENT_FILE_DOWNLOAD_BACKEND_ARGUMENTS',
    help_text=_(
        'Arguments to pass to the '
        'DOCUMENT_DOWNLOADS_DOCUMENT_FILE_DOWNLOAD_BACKEND.'
    )
)
setting_message_body_template = setting_namespace.do_setting_add(
    default=DEFAULT_DOCUMENT_FILE_DOWNLOAD_MESSAGE_BODY,
    global_name='DOCUMENT_FILE_DOWNLOAD_MESSAGE_BODY',
    help_text=format_lazy(
        _(
            message='Template for the document download message body text. '
            'Can include HTML. Available variables: {}'
        ), ', '.join(DocumentFileCompressor.context_key_list)
    )
)
setting_message_subject_template = setting_namespace.do_setting_add(
    default=DEFAULT_DOCUMENT_FILE_DOWNLOAD_MESSAGE_SUBJECT,
    global_name='DOCUMENT_FILE_DOWNLOAD_MESSAGE_SUBJECT',
    help_text=format_lazy(
        _(
            message='Template for the document download message subject '
            'line. Can\'t include HTML. Available variables: {}'
        ), ', '.join(DocumentFileCompressor.context_key_list)
    )
)
