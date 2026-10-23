from django.apps import apps
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.models import AccessControlList
from mayan.apps.documents.models.document_models import Document


class DuplicateBackendEntryBusinessLogicMixin:
    def get_document_count(self, permission, user):
        queryset = self.get_documents(permission=permission, user=user)

        return queryset.count()

    get_document_count.short_description = _(message='Document count')

    def get_documents(self, permission, user):
        return AccessControlList.objects.restrict_queryset(
            permission=permission, queryset=self.documents, user=user
        )


class StoredDuplicateBackendBusinessLogicMixin:
    def get_document_count(self, permission, user):
        queryset = self.get_documents(permission=permission, user=user)

        return queryset.count()

    get_document_count.short_description = _(message='Document count')

    def get_documents(self, permission, user):
        DuplicateSourceDocument = apps.get_model(
            app_label='duplicates', model_name='DuplicateSourceDocument'
        )

        queryset_as_duplicate = Document.objects.filter(
            as_duplicate__stored_backend=self
        )
        queryset_as_source = Document.objects.filter(
            duplicate_backend_entries__stored_backend=self
        )
        queryset_complete = queryset_as_duplicate | queryset_as_source

        queryset_restricted = AccessControlList.objects.restrict_queryset(
            permission=permission, queryset=queryset_complete, user=user
        )

        return DuplicateSourceDocument.valid.filter(
            pk__in=queryset_restricted
        )
