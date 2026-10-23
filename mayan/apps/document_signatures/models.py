import logging

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from model_utils.managers import InheritanceManager

from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.django_gpg.exceptions import VerificationError
from mayan.apps.django_gpg.models import Key
from mayan.apps.documents.models.document_file_models import DocumentFile
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import (
    EventManagerMethodAfter, EventManagerSave
)
from mayan.apps.storage.classes import DefinedStorageLazy

from .events import (
    event_detached_signature_deleted, event_detached_signature_uploaded
)
from .literals import STORAGE_NAME_DOCUMENT_SIGNATURES_DETACHED_SIGNATURE
from .managers import DetachedSignatureManager, EmbeddedSignatureManager
from .model_mixins import SignatureBaseModelBusinessLogicMixin
from .utils import upload_to

logger = logging.getLogger(name=__name__)


class SignatureBaseModel(SignatureBaseModelBusinessLogicMixin, models.Model):
    document_file = models.ForeignKey(
        editable=False, on_delete=models.CASCADE, related_name='signatures',
        to=DocumentFile, verbose_name=_(message='Document file')
    )
    date_time = models.DateTimeField(
        blank=True, editable=False, null=True, verbose_name=_(
            message='Date and time signed'
        )
    )
    key_id = models.CharField(
        help_text=_(
            message='ID of the key that will be used to sign the document.'
        ), max_length=40, verbose_name=_(message='Key ID')
    )
    signature_id = models.CharField(
        blank=True, editable=False, null=True, max_length=64,
        verbose_name=_(message='Signature ID')
    )
    public_key_fingerprint = models.CharField(
        blank=True, editable=False, null=True, max_length=40,
        verbose_name=_(message='Public key fingerprint')
    )

    objects = InheritanceManager()

    class Meta:
        ordering = ('pk',)
        verbose_name = _(message='Document file signature')
        verbose_name_plural = _(message='Document file signatures')

    def __str__(self):
        return self.signature_id or '{} - {}'.format(
            self.date_time, self.key_id
        )

    def get_absolute_url(self):
        return reverse(
            kwargs={'signature_id': self.pk},
            viewname='signatures:document_file_signature_detail'
        )


class DetachedSignature(ExtraDataModelMixin, SignatureBaseModel):
    signature_file = models.FileField(
        blank=True, help_text=_(
            message='Signature file previously generated.'
        ), null=True, storage=DefinedStorageLazy(
            name=STORAGE_NAME_DOCUMENT_SIGNATURES_DETACHED_SIGNATURE
        ), upload_to=upload_to, verbose_name=_(message='Signature file')
    )

    objects = DetachedSignatureManager()

    class Meta:
        verbose_name = _(message='Document file detached signature')
        verbose_name_plural = _(message='Document file detached signatures')

    def __str__(self):
        return '{}-{}'.format(
            self.document_file, _(message='signature')
        )

    @method_event(
        event_manager_class=EventManagerMethodAfter,
        event=event_detached_signature_deleted,
        target='document_file'
    )
    def delete(self, *args, **kwargs):
        signature_file_name = self.signature_file.name
        if signature_file_name:
            self.signature_file.close()
            self.signature_file.storage.delete(name=signature_file_name)
        super().delete(*args, **kwargs)

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'action_object': 'self',
            'event': event_detached_signature_uploaded,
            'target': 'document_file'
        }
    )
    def save(self, *args, **kwargs):
        with self.document_file.open() as file_object:
            try:
                verify_result = Key.objects.verify_file(
                    file_object=file_object,
                    signature_file=self.signature_file
                )
            except VerificationError as exception:
                logger.debug(
                    'detached signature verification error; %s', exception
                )
            else:
                self.signature_file.seek(0)

                self.date_time = getattr(verify_result, 'date_time', None)
                self.key_id = verify_result.key_id
                self.signature_id = verify_result.signature_id
                self.public_key_fingerprint = verify_result.pubkey_fingerprint

        return super().save(*args, **kwargs)


class EmbeddedSignature(SignatureBaseModel):
    objects = EmbeddedSignatureManager()

    class Meta:
        verbose_name = _(message='Document file embedded signature')
        verbose_name_plural = _(message='Document file embedded signatures')

    def save(self, *args, **kwargs):
        logger.debug(msg='checking for embedded signature')

        if self.pk:
            raw = True
        else:
            raw = False

        with self.document_file.open(raw=raw) as file_object:
            try:
                verify_result = Key.objects.verify_file(
                    file_object=file_object
                )
            except VerificationError as exception:
                logger.debug(
                    'embedded signature verification error; %s', exception
                )
            else:
                self.date_time = getattr(verify_result, 'date_time', None)
                self.key_id = verify_result.key_id
                self.signature_id = verify_result.signature_id
                self.public_key_fingerprint = verify_result.pubkey_fingerprint

                return super().save(*args, **kwargs)
