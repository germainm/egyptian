from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.models import AccessControlList
from mayan.apps.documents.models.document_models import Document
from mayan.apps.documents.permissions import permission_document_view


class CabinetBusinessLogicMixin:
    def _get_documents(self):
        return Document.valid.filter(
            pk__in=self.documents.values('pk')
        )

    def document_add(self, document, user):
        return self._document_add(document=document, user=user)

    def document_remove(self, document, user):
        return self._document_remove(document=document, user=user)

    def get_descendants_document_count(self, user):
        queryset_documents = Document.valid.filter(
            cabinets__in=self.get_descendants(
                include_self=True
            )
        ).distinct()

        queryset_documents_filtered = AccessControlList.objects.restrict_queryset(
            permission=permission_document_view,
            queryset=queryset_documents, user=user
        )

        return queryset_documents_filtered.count()

    def get_document_count(self, user):
        return self.get_documents(
            permission=permission_document_view, user=user
        ).count()

    def get_documents(self, permission, user):
        return AccessControlList.objects.restrict_queryset(
            permission=permission, queryset=self._get_documents(),
            user=user
        )

    def get_full_path(self):
        result = []
        for node in self.get_ancestors(include_self=True):
            result.append(node.label)

        return ' / '.join(result)
    get_full_path.help_text = _(
        message='The path to the cabinet including all ancestors.'
    )
    get_full_path.short_description = _(message='Full path')
