from django.utils.translation import gettext_lazy as _

DEFAULT_DOCUMENT_VERSION_EXPORT_RESOLUTION = 300.0

DOCUMENT_VERSION_EXPORT_MESSAGE_BODY = _(
    message='Document version "%(document_version)s" has been '
    'exported and is available for download using the '
    'link: %(download_url)s or from '
    'the downloads area (%(download_list_url)s).'
)
DOCUMENT_VERSION_EXPORT_MESSAGE_SUBJECT = _(message='Document version exported.')
DOCUMENT_VERSION_EXPORT_MIMETYPE = 'application/pdf'

ERROR_LOG_DOMAIN_NAME = 'document_exports'
