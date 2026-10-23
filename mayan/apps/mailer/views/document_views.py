from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.models.document_models import Document

from ..icons import icon_document_link_send_single

from .base import MailingObjectLinkSendView


class MailDocumentLinkView(MailingObjectLinkSendView):
    pk_url_kwarg = 'document_id'
    source_queryset = Document.valid.all()
    success_message = _(
        message='%(count)d document link queued for email delivery'
    )
    success_message_plural = _(
        message='%(count)d document links queued for email delivery'
    )
    title = _(message='Email document link')
    title_document = _(message='Email link for document: %s')
    title_plural = _(message='Email document links')
    view_icon = icon_document_link_send_single
