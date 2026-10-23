from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.models.document_version_models import (
    DocumentVersion
)

from ..icons import (
    icon_document_version_attachment_send_single,
    icon_document_version_link_send_single
)

from .base import MailingObjectAttachmentSendView, MailingObjectLinkSendView


class MailDocumentVersionAttachmentView(MailingObjectAttachmentSendView):
    pk_url_kwarg = 'document_version_id'
    source_queryset = DocumentVersion.valid.all()
    success_message = _(
        message='%(count)d document version queued for email delivery'
    )
    success_message_plural = _(
        message='%(count)d document versions queued for email delivery'
    )
    title = _(message='Email document version')
    title_document = _(message='Email document version: %s')
    title_plural = _(message='Email documents version')
    view_icon = icon_document_version_attachment_send_single


class MailDocumentVersionLinkView(MailingObjectLinkSendView):
    pk_url_kwarg = 'document_version_id'
    source_queryset = DocumentVersion.valid.all()
    success_message = _(
        message='%(count)d document version link queued for email delivery'
    )
    success_message_plural = _(
        message='%(count)d document version links queued for email delivery'
    )
    title = _(message='Email document version link')
    title_document = _(message='Email link for document version: %s')
    title_plural = _(message='Email document version links')
    view_icon = icon_document_version_link_send_single
