from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.models import AccessControlList
from mayan.apps.documents.models.document_models import Document
from mayan.apps.documents.permissions import permission_document_view
from mayan.apps.documents.views.document_views import DocumentListView
from mayan.apps.views.generics import SingleObjectListView
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from ..icons import (
    icon_document_duplicate_backend_document_list,
    icon_document_duplicate_backend_list
)


class DocumentDuplicateBackendDocumentListView(DocumentListView):
    view_icon = icon_document_duplicate_backend_document_list

    def get_backend_entry(self):
        return get_object_or_404(
            klass=self.get_backend_entry_queryset(),
            pk=self.kwargs['backend_entry_id']
        )

    def get_backend_entry_queryset(self):
        document = self.get_document()
        return document.duplicate_backend_entries.all()

    def get_document(self):
        queryset_documents = Document.valid.all()
        queryset_restricted = AccessControlList.objects.restrict_queryset(
            permission=permission_document_view,
            queryset=queryset_documents, user=self.request.user
        )

        return get_object_or_404(
            klass=queryset_restricted, pk=self.kwargs['document_id']
        )

    def get_extra_context(self):
        context = super().get_extra_context()

        backend_entry = self.get_backend_entry()
        document = self.get_document()

        context.update(
            {
                'no_results_icon': icon_document_duplicate_backend_document_list,
                'no_results_text': _(
                    message='Documents that match the duplication logic of '
                    'this backend, in relation to the selected document.'
                ),
                'no_results_title': _(
                    message='There are no duplicates for this backend and '
                    'document combination'
                ),
                'object': document,
                'title': _(
                    message='Duplicates of document: %(document)s, using '
                    'backend: %(backend)s'
                ) % {
                    'backend': backend_entry.stored_backend,
                    'document': document
                }
            }
        )

        return context

    def get_source_queryset(self):
        backend_entry = self.get_backend_entry()
        queryset_documents = backend_entry.documents.values('pk')

        return Document.valid.filter(pk__in=queryset_documents)


class DocumentDuplicateBackendListView(
    ExternalObjectViewMixin, SingleObjectListView
):
    external_object_permission = permission_document_view
    external_object_pk_url_kwarg = 'document_id'
    external_object_queryset = Document.valid.all()
    view_icon = icon_document_duplicate_backend_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_document_duplicate_backend_document_list,
            'no_results_text': _(
                message='Duplicate backend entries list the documents that '
                'match the duplication logic of a backend, for this '
                'document.'
            ),
            'no_results_title': _(
                message='There are no duplicate backends for this document'
            ),
            'object': self.external_object,
            'title': _(
                message='Duplicate backends for document: %s'
            ) % self.external_object
        }

    def get_source_queryset(self):
        return self.external_object.duplicate_backend_entries.all()
