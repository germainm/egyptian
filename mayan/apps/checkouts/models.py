import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.documents.models.document_models import Document
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import EventManagerMethodAfter

from .events import (
    event_document_auto_checked_in, event_document_checked_in,
    event_document_checked_out, event_document_forcefully_checked_in
)
from .exceptions import DocumentAlreadyCheckedOut
from .managers import (
    DocumentCheckoutBusinessLogicManager, DocumentCheckoutManager
)
from .model_mixins import CheckedOutDocumentBusinessLogicMixin

logger = logging.getLogger(name=__name__)


class DocumentCheckout(ExtraDataModelMixin, models.Model):
    document = models.OneToOneField(
        on_delete=models.CASCADE, to=Document, related_name='checkout',
        verbose_name=_(message='Document')
    )
    checkout_datetime = models.DateTimeField(
        auto_now_add=True, verbose_name=_(message='Check out date and time')
    )
    expiration_datetime = models.DateTimeField(
        help_text=_(
            message='Amount of time to hold the document checked out in '
            'minutes.'
        ), verbose_name=_(message='Check out expiration date and time')
    )
    user = models.ForeignKey(
        on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL,
        verbose_name=_(message='User')
    )
    block_new_file = models.BooleanField(
        default=True, help_text=_(
            message='Do not allow new file of this document to be uploaded.'
        ), verbose_name=_(message='Block new file upload')
    )

    objects = DocumentCheckoutManager()
    business_logic = DocumentCheckoutBusinessLogicManager()

    class Meta:
        ordering = ('pk',)
        verbose_name = _(message='Document checkout')
        verbose_name_plural = _(message='Document checkouts')

    def __str__(self):
        return str(self.document)

    def clean(self):
        if self.expiration_datetime < now():
            raise ValidationError(
                message=_(
                    message='Check out expiration date and time must be in '
                    'the future.'
                )
            )

    @method_event(event_manager_class=EventManagerMethodAfter)
    def delete(self, user=None):
        self._event_target = self.document
        self._event_actor = user or getattr(self, '_event_actor', None)

        if self._event_actor:
            if self._event_actor == self.user:
                self._event_type = event_document_checked_in
            else:
                self._event_type = event_document_forcefully_checked_in
        else:
            self._event_type = event_document_auto_checked_in

        return super().delete()

    def get_absolute_url(self):
        return reverse(
            kwargs={'document_id': self.document_id},
            viewname='checkouts:check_out_info'
        )

    def natural_key(self):
        return self.document.natural_key()
    natural_key.dependencies = ['documents.Document']

    def save(self, *args, **kwargs):
        is_new = not self.pk
        if not is_new or self.document.is_checked_out():
            raise DocumentAlreadyCheckedOut

        result = super().save(*args, **kwargs)
        if is_new:
            event_document_checked_out.commit(
                actor=self.user, target=self.document
            )

            logger.debug(
                'Document "%s" checked out by user "%s"',
                self.document, self.user
            )

        return result


class CheckedOutDocument(CheckedOutDocumentBusinessLogicMixin, Document):
    class Meta:
        proxy = True
