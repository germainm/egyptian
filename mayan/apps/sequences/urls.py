from django.urls import re_path

from .api_views import (
    APISequenceDetailView, APISequenceListView, APISequenceValueNextView
)
from .views import (
    DocumentTypeSequenceAddRemoveView, SequenceBackendSelectionView,
    SequenceCreateView, SequenceDeleteView, SequenceDocumentTypeAddRemoveView,
    SequenceEditView, SequenceListView, SequenceResetView
)

urlpatterns = [
    re_path(
        route=r'^document_types/(?P<document_type_id>\d+)/sequences/$',
        name='document_type_sequence_list',
        view=DocumentTypeSequenceAddRemoveView.as_view()
    ),
    re_path(
        route=r'^sequences/$', name='sequence_list',
        view=SequenceListView.as_view()
    ),
    re_path(
        route=r'^sequences/backend/selection/$',
        name='sequence_backend_selection',
        view=SequenceBackendSelectionView.as_view()
    ),
    re_path(
        route=r'^sequences/(?P<backend_path>[a-zA-Z0-9_.]+)/create/$',
        name='sequence_create', view=SequenceCreateView.as_view()
    ),
    re_path(
        route=r'^sequences/(?P<sequence_id>\d+)/delete/$',
        name='sequence_delete', view=SequenceDeleteView.as_view()
    ),
    re_path(
        route=r'^sequences/(?P<sequence_id>\d+)/document_types/$',
        name='sequence_document_type_list',
        view=SequenceDocumentTypeAddRemoveView.as_view()
    ),
    re_path(
        route=r'^sequences/(?P<sequence_id>\d+)/edit/$',
        name='sequence_edit', view=SequenceEditView.as_view()
    ),
    re_path(
        route=r'^sequences/(?P<sequence_id>\d+)/reset/$',
        name='sequence_reset', view=SequenceResetView.as_view()
    )
]

api_urls = [
    re_path(
        route=r'^sequences/$', name='sequence-list',
        view=APISequenceListView.as_view()
    ),
    re_path(
        route=r'^sequences/(?P<sequence_id>[0-9]+)/$',
        name='sequence-detail', view=APISequenceDetailView.as_view()
    ),
    re_path(
        route=r'^sequences/(?P<sequence_id>[0-9]+)/value/next/$',
        name='sequence-value-next', view=APISequenceValueNextView.as_view()
    )
]
