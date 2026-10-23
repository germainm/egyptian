from datetime import timedelta
import logging

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from mayan.apps.databases.classes import ModelQueryFields

from .literals import (
    DOCUMENT_TYPE_RETENTION_ITERATOR_CHUNK_SIZE,
    DOCUMENT_TYPE_STUB_ITERATOR_CHUNK_SIZE, ERROR_LOG_DOMAIN_NAME
)
from .settings import (
    setting_recently_accessed_document_count,
    setting_recently_created_document_count
)

logger = logging.getLogger(name=__name__)


class DocumentManager(models.Manager):
    def get_by_natural_key(self, uuid):
        return self.get(
            uuid=str(uuid)
        )


class DocumentFileManager(models.Manager):
    def get_by_natural_key(self, checksum, document_natural_key):
        Document = apps.get_model(
            app_label='documents', model_name='Document'
        )
        try:
            document = Document.objects.get_by_natural_key(
                *document_natural_key
            )
        except Document.DoesNotExist:
            raise self.model.DoesNotExist

        return self.get(document__pk=document.pk, checksum=checksum)


class DocumentFilePageManager(models.Manager):
    def get_by_natural_key(self, page_number, document_file_natural_key):
        DocumentFile = apps.get_model(
            app_label='documents', model_name='DocumentFile'
        )
        try:
            document_file = DocumentFile.objects.get_by_natural_key(
                *document_file_natural_key
            )
        except DocumentFile.DoesNotExist:
            raise self.model.DoesNotExist

        return self.get(
            document_file__pk=document_file.pk, page_number=page_number
        )


class DocumentTypeManager(models.Manager):
    def _do_document_delete(self, document, to_trash=True):
        try:
            document.delete(to_trash=to_trash)
        except Exception as exception:
            logger.error(
                'Error deleting document with id: %d; %s', document.pk,
                exception, exc_info=True
            )

            error_log_text = _(
                message='Error deleting the document; %(exception)s'
            ) % {'exception': exception}

            document.error_log.create(
                domain_name=ERROR_LOG_DOMAIN_NAME, text=error_log_text
            )

    def check_delete_periods(self):
        logger.debug(msg='Executing')

        queryset_document_types_with_deletion_setup = self.filter(
            delete_time_period__isnull=False, delete_time_unit__isnull=False
        ).only('id')

        for document_type in queryset_document_types_with_deletion_setup:
            logger.debug(
                'Checking deletion period of document type: %s',
                document_type
            )
            delta = timedelta(
                **{
                    document_type.delete_time_unit: document_type.delete_time_period
                }
            )
            logger.debug(
                'Document type: %s, has a deletion period delta of: %s',
                document_type, delta
            )

            cutoff = now() - delta

            queryset_documents_to_delete = document_type.documents.filter(
                in_trash=True, trashed_date_time__lt=cutoff
            ).only('id', 'in_trash', 'trashed_date_time')

            for document in queryset_documents_to_delete.iterator(chunk_size=DOCUMENT_TYPE_RETENTION_ITERATOR_CHUNK_SIZE):
                logger.debug(
                    'Document "%s" with id: %d, trashed on: %s, exceeded '
                    'delete period', document, document.id,
                    document.trashed_date_time
                )
                self._do_document_delete(document=document)

        logger.debug(msg='Finished')

    def check_trash_periods(self):
        logger.debug(msg='Executing')

        queryset_document_types_with_trashed_setup = self.filter(
            trash_time_period__isnull=False, trash_time_unit__isnull=False
        ).only('id')

        for document_type in queryset_document_types_with_trashed_setup:
            logger.debug(
                'Checking trash period of document type: %s', document_type
            )

            delta = timedelta(
                **{
                    document_type.trash_time_unit: document_type.trash_time_period
                }
            )
            logger.debug(
                'Document type: %s, has a trash period delta of: %s',
                document_type, delta
            )

            cutoff = now() - delta

            queryset_documents_to_trash = document_type.documents.filter(
                datetime_created__lt=cutoff, in_trash=False
            ).only('id', 'datetime_created', 'in_trash')

            for document in queryset_documents_to_trash.iterator(chunk_size=DOCUMENT_TYPE_RETENTION_ITERATOR_CHUNK_SIZE):
                logger.debug(
                    'Document "%s" with id: %d, added on: %s, exceeded '
                    'trash period.', document, document.id,
                    document.datetime_created
                )
                self._do_document_delete(document=document)

        logger.debug(msg='Finished')

    def document_stubs_delete(self):
        logger.debug(msg='Executing')

        for document_type in self.filter(document_stub_pruning_enabled=True):
            logger.debug(
                'Checking expired document stubs of document type: %s',
                document_type
            )

            delta = timedelta(
                seconds=document_type.document_stub_expiration_interval
            )

            cutoff = now() - delta

            queryset_stale_stub_documents = document_type.documents.filter(
                datetime_created__lt=cutoff, is_stub=True
            ).only('id')

            logger.debug(
                'Deleting %d document stubs', queryset_stale_stub_documents.count()
            )

            for stale_stub_document in queryset_stale_stub_documents.iterator(chunk_size=DOCUMENT_TYPE_STUB_ITERATOR_CHUNK_SIZE):
                self._do_document_delete(
                    document=stale_stub_document, to_trash=False
                )

        logger.debug(msg='Finished')

    def get_by_natural_key(self, label):
        return self.get(label=label)


class RecentlyAccessedDocumentManager(models.Manager):
    def get_by_natural_key(
        self, datetime_accessed, document_natural_key, user_natural_key
    ):
        Document = apps.get_model(
            app_label='documents', model_name='Document'
        )
        User = get_user_model()
        try:
            document = Document.objects.get_by_natural_key(
                *document_natural_key
            )
        except Document.DoesNotExist:
            raise self.model.DoesNotExist
        else:
            try:
                user = User.objects.get_by_natural_key(*user_natural_key)
            except User.DoesNotExist:
                raise self.model.DoesNotExist

        return self.get(
            document__pk=document.pk, user__pk=user.pk,
            datetime_accessed=datetime_accessed
        )


class TrashCanManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(in_trash=True)


class TrashCanQuerySet(models.QuerySet):
    def delete(self, to_trash=True):
        for instance in self:
            instance.delete(to_trash=to_trash)


class ValidDocumentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            in_trash=False
        )


class ValidDocumentFileManager(models.Manager):
    def get_queryset(self):
        return models.QuerySet(
            model=self.model, using=self._db
        ).filter(document__in_trash=False).select_related('document')


class ValidDocumentFilePageManager(models.Manager):
    def get_queryset(self):
        return models.QuerySet(
            model=self.model, using=self._db
        ).filter(
            document_file__document__in_trash=False
        ).select_related('document_file', 'document_file__document')


class ValidDocumentVersionManager(models.Manager):
    def get_queryset(self):
        return models.QuerySet(
            model=self.model, using=self._db
        ).filter(document__in_trash=False).select_related('document')


class ValidDocumentVersionPageManager(models.Manager):
    def get_queryset(self):
        return models.QuerySet(
            model=self.model, using=self._db
        ).filter(
            document_version__document__in_trash=False
        ).select_related('document_version', 'document_version__document')


class ValidRecentlyAccessedDocumentManager(models.Manager):
    def add_document_for_user(self, user, document):
        if user.is_authenticated:
            new_recent, created = self.model.objects.get_or_create(
                user=user, document=document
            )
            if not created:
                new_recent.save(
                    update_fields=('datetime_accessed',)
                )

            queryset_recent_to_delete = self.filter(
                user=user
            ).only('pk').values_list('pk', flat=True)[
                setting_recently_accessed_document_count.value:
            ]

            self.filter(pk__in=queryset_recent_to_delete).delete()

        return new_recent

    def get_for_user(self, user):
        RecentlyAccessedDocumentProxy = apps.get_model(
            app_label='documents', model_name='RecentlyAccessedDocumentProxy'
        )

        if user.is_authenticated:
            return RecentlyAccessedDocumentProxy.valid.filter(
                recent__user=user
            ).order_by('-recent__datetime_accessed')
        else:
            return RecentlyAccessedDocumentProxy.objects.none()

    def get_queryset(self):
        return super().get_queryset().filter(document__in_trash=False)


class ValidRecentlyCreatedDocumentManager(models.Manager):
    def get_queryset(self):
        Document = apps.get_model(
            app_label='documents', model_name='Document'
        )

        queryset_valid = ModelQueryFields.get(
            model=Document
        ).get_queryset(manager_name='valid')

        queryset_recent = queryset_valid.order_by('-datetime_created')[
            :setting_recently_created_document_count.value
        ].only('pk').values_list('pk', flat=True)

        queryset_final = super().get_queryset().filter(
            pk__in=queryset_recent
        ).order_by('-datetime_created')

        return queryset_final
