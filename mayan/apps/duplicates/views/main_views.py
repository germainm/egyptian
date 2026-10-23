from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.permissions import permission_document_view
from mayan.apps.documents.views.document_views import DocumentListView
from mayan.apps.views.generics import SingleObjectListView
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from ..icons import (
    icon_duplicate_backend_document_list, icon_duplicate_backend_list
)
from ..models import StoredDuplicateBackend


class DuplicateBackendDocumentListView(
    ExternalObjectViewMixin, DocumentListView
):
    external_object_class = StoredDuplicateBackend
    external_object_pk_url_kwarg = 'stored_duplicated_backend_id'
    view_icon = icon_duplicate_backend_document_list

    def get_extra_context(self):
        context = super().get_extra_context()

        context.update(
            {
                'no_results_icon': icon_duplicate_backend_document_list,
                'no_results_text': _(
                    message='Documents that match the duplication logic of '
                    'this backend.'
                ),
                'no_results_title': _(
                    message='There are no duplicates for this backend'
                ),
                'object': self.external_object,
                'title': _(
                    message='Documents for duplicate backend: %s'
                ) % self.external_object
            }
        )

        return context

    def get_source_queryset(self):
        stored_duplicate_backend = self.external_object

        return stored_duplicate_backend.get_documents(
            permission=permission_document_view, user=self.request.user
        )


class DuplicatesBackendListView(SingleObjectListView):
    view_icon = icon_duplicate_backend_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_duplicate_backend_list,
            'no_results_text': _(
                message='Duplicate backends scan documents using a specific '
                'duplication logic.'
            ),
            'no_results_title': _(
                message='There are no duplicate backends'
            ),
            'title': _(message='Duplicate backends')
        }

    def get_source_queryset(self):
        return StoredDuplicateBackend.objects.all()
