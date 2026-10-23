import uuid

from django.db import models, transaction
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.signals import signal_mayan_pre_save
from mayan.apps.databases.model_mixins import ExtraDataModelMixin

from ..events import event_document_trashed, event_trashed_document_deleted
from ..literals import DEFAULT_LANGUAGE
from ..managers import (
    DocumentManager, TrashCanManager, ValidDocumentManager,
    ValidRecentlyCreatedDocumentManager
)
from ..settings import setting_language

from .document_model_mixins import DocumentBusinessLogicMixin
from .document_type_models import DocumentType
from .model_mixins import HooksModelMixin

__all__ = ('Document', 'DocumentSearchResult',)


class Document(
    DocumentBusinessLogicMixin, ExtraDataModelMixin, HooksModelMixin,
    models.Model
):
    _hooks_pre_create = []
    _ordering_fields = ('datetime_created', 'label')

    file_latest = models.OneToOneField(
        blank=True, null=True, on_delete=models.SET_NULL, to='DocumentFile',
        related_name='document_latest', verbose_name=_(
            message='Latest document file'
        )
    )
    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, help_text=_(
            message='UUID of a document, universally Unique ID. An unique '
            'identifier generated for each document.'
        ), verbose_name=_(message='UUID')
    )
    document_type = models.ForeignKey(
        help_text=_(message='The document type of the document.'),
        on_delete=models.CASCADE, related_name='documents', to=DocumentType,
        verbose_name=_(message='Document type')
    )
    label = models.CharField(
        blank=True, db_index=True, default='', max_length=255,
        help_text=_(
            message='A short text identifying the document. By default, '
            'will be set to the filename of the first file uploaded to the '
            'document.'
        ),
        verbose_name=_(message='Label')
    )
    description = models.TextField(
        blank=True, default='', help_text=_(
            message='An optional short text describing a document.'
        ), verbose_name=_(message='Description')
    )
    datetime_created = models.DateTimeField(
        auto_now_add=True, db_index=True, help_text=_(
            message='The date and time of the document creation.'
        ), verbose_name=_(message='Created')
    )
    language = models.CharField(
        blank=True, default=DEFAULT_LANGUAGE, help_text=_(
            message='The primary language in the document.'
        ), max_length=8, verbose_name=_(message='Language')
    )
    in_trash = models.BooleanField(
        db_index=True, default=False, help_text=_(
            message='Whether or not this document is in the trash.'
        ), editable=False, verbose_name=_(message='In trash?')
    )
    trashed_date_time = models.DateTimeField(
        blank=True, editable=True, help_text=_(
            message='The server date and time when the document was moved '
            'to the trash.'
        ), null=True, verbose_name=_(message='Date and time trashed')
    )
    is_stub = models.BooleanField(
        db_index=True, default=True, editable=False, help_text=_(
            message='A document stub is a document with an entry on the '
            'database but no file uploaded. This could be an interrupted '
            'upload or a deferred upload via the API.'
        ), verbose_name=_(message='Is stub?')
    )
    version_active = models.OneToOneField(
        blank=True, null=True, on_delete=models.SET_NULL,
        to='DocumentVersion', related_name='document_active', verbose_name=_(
            message='Active document version'
        )
    )

    objects = DocumentManager()
    trash = TrashCanManager()
    valid = ValidDocumentManager()

    class Meta:
        ordering = ('label',)
        verbose_name = _(message='Document')
        verbose_name_plural = _(message='Documents')

    def __str__(self):
        return self.get_label()

    def delete(self, *args, **kwargs):
        to_trash = kwargs.pop('to_trash', True)
        user = self.__dict__.pop('_event_actor', None)

        if not self.in_trash and to_trash:
            self.in_trash = True
            self.trashed_date_time = now()
            with transaction.atomic():
                self._event_ignore = True
                self.save(
                    update_fields=('in_trash', 'trashed_date_time')
                )

            event_document_trashed.commit(actor=user, target=self)
        else:
            with transaction.atomic():
                for document_file in self.files.all():
                    document_file.delete()

                super().delete(*args, **kwargs)

            event_trashed_document_deleted.commit(
                actor=user, target=self.document_type
            )

    def get_absolute_url(self):
        return reverse(
            kwargs={'document_id': self.pk},
            viewname='documents:document_preview'
        )

    def natural_key(self):
        return (self.uuid,)
    natural_key.dependencies = ['documents.DocumentType']

    def save(self, *args, **kwargs):
        user = getattr(self, '_event_actor', None)
        new_document = not self.pk

        self.description = self.description or ''
        self.label = self.label or ''
        self.language = self.language or setting_language.value

        signal_mayan_pre_save.send(instance=self, sender=Document, user=user)

        super().save(*args, **kwargs)

        self.__dict__.pop('_event_ignore', False)

        if new_document:
            if user:
                self.add_as_recent_document_for_user(user=user)


class DocumentSearchResult(Document):
    class Meta:
        proxy = True


class RecentlyCreatedDocument(Document):
    objects = models.Manager()
    valid = ValidRecentlyCreatedDocumentManager()

    class Meta:
        proxy = True
