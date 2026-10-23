from itertools import islice
import logging

from django.apps import apps
from django.db import models
from django.db.models import Q, Value

from mayan.apps.acls.models import AccessControlList
from mayan.apps.lock_manager.backends.base import LockingBackend
from mayan.apps.lock_manager.exceptions import LockError

from .classes import DuplicateBackend
from .literals import BULK_CREATE_BATCH_SIZE

logger = logging.getLogger(name=__name__)


class DuplicateBackendEntryManager(models.Manager):
    def clean_empty_duplicate_lists(self):
        self.filter(documents=None).delete()

    def get_duplicated_documents(self, permission=None, user=None):
        DuplicateSourceDocument = apps.get_model(
            app_label='duplicates', model_name='DuplicateSourceDocument'
        )
        DuplicateTargetDocument = apps.get_model(
            app_label='duplicates', model_name='DuplicateTargetDocument'
        )

        queryset_target_documents = DuplicateTargetDocument.valid.all()

        if permission:
            queryset_target_documents = AccessControlList.objects.restrict_queryset(
                queryset=queryset_target_documents, permission=permission,
                user=user
            )

        queryset = self.filter(documents__in=queryset_target_documents).only(
            'document_id'
        ).values('document_id')

        return DuplicateSourceDocument.valid.filter(pk__in=queryset)

    def get_duplicates_of(self, document, permission=None, user=None):
        DuplicateTargetDocument = apps.get_model(
            app_label='duplicates', model_name='DuplicateTargetDocument'
        )

        queryset = DuplicateTargetDocument.valid.none()

        when_list = []

        for entry in self.filter(document=document).all():
            queryset = queryset | DuplicateTargetDocument.valid.filter(
                pk__in=entry.documents.only('pk').values('pk')
            )

            when_list.append(
                models.When(
                    Q(
                        pk__in=entry.documents.only('pk').values('pk')
                    ),
                    then=Value(
                        value=str(entry.stored_backend)
                    )
                )
            )

        queryset = queryset.annotate(
            backend=models.Case(
                *when_list, output_field=models.CharField()
            )
        )

        if permission:
            queryset = AccessControlList.objects.restrict_queryset(
                permission=permission, queryset=queryset, user=user
            )

        return queryset


class StoredDuplicateBackendManager(models.Manager):
    def scan_document(self, document):
        lock_name = 'duplicates__scan_document-{}'.format(document.pk)
        try:
            logger.debug('trying to acquire lock: %s', lock_name)
            lock = LockingBackend.get_backend().acquire_lock(name=lock_name)
            logger.debug('acquired lock: %s', lock_name)
            try:
                DuplicateBackendEntry = apps.get_model(
                    app_label='duplicates', model_name='DuplicateBackendEntry'
                )

                for backend_path, backend_class in DuplicateBackend.get_all():
                    if backend_class.verify(document=document):

                        stored_backend, created = self.get_or_create(
                            backend_path=backend_path
                        )
                        duplicates = stored_backend.get_backend_instance().process(
                            document=document
                        )

                        if duplicates.exists():
                            duplicates_entry, created = stored_backend.duplicate_entries.get_or_create(
                                document=document
                            )

                            bulk_create_list = (
                                duplicates_entry.documents.through(
                                    duplicatebackendentry_id=duplicates_entry.pk,
                                    document=duplicate
                                ) for duplicate in duplicates
                            )

                            while True:
                                batch = list(
                                    islice(
                                        bulk_create_list,
                                        BULK_CREATE_BATCH_SIZE
                                    )
                                )

                                if not batch:
                                    break

                                duplicates_entry.documents.through.objects.bulk_create(
                                    batch_size=BULK_CREATE_BATCH_SIZE,
                                    ignore_conflicts=True, objs=batch
                                )

                            bulk_create_list = (
                                DuplicateBackendEntry(
                                    stored_backend=stored_backend,
                                    document=duplicate,
                                ) for duplicate in duplicates.filter(
                                    duplicate_backend_entries__stored_backend=None
                                )
                            )

                            while True:
                                batch = list(
                                    islice(
                                        bulk_create_list,
                                        BULK_CREATE_BATCH_SIZE
                                    )
                                )

                                if not batch:
                                    break

                                DuplicateBackendEntry.objects.bulk_create(
                                    batch_size=BULK_CREATE_BATCH_SIZE,
                                    ignore_conflicts=True, objs=batch
                                )

                            duplicate_entries = stored_backend.duplicate_entries.filter(
                                document__in=duplicates
                            )

                            bulk_create_list = (
                                document.as_duplicate.through(
                                    duplicatebackendentry_id=duplicate_entry.pk,
                                    document_id=document.pk
                                ) for duplicate_entry in duplicate_entries
                            )

                            while True:
                                batch = list(
                                    islice(
                                        bulk_create_list,
                                        BULK_CREATE_BATCH_SIZE
                                    )
                                )

                                if not batch:
                                    break

                                document.as_duplicate.through.objects.bulk_create(
                                    batch_size=BULK_CREATE_BATCH_SIZE,
                                    ignore_conflicts=True, objs=batch
                                )
                        else:
                            stored_backend.duplicate_entries.filter(
                                document=document
                            ).delete()

                            document.as_duplicate.filter(
                                stored_backend=stored_backend
                            ).delete()
                    else:
                        stored_backend.duplicate_entries.filter(
                            documents=document
                        ).delete()

                        document.as_duplicate.filter(
                            stored_backend=stored_backend
                        ).delete()
            finally:
                lock.release()
        except LockError:
            logger.debug('unable to obtain lock: %s' % lock_name)
            raise
