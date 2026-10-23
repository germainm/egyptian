import logging

from mayan.apps.rest_api import generics
from mayan.apps.rest_api.api_view_mixins import ExternalObjectAPIViewMixin

from ..models.document_models import Document
from ..models.document_type_models import DocumentType
from ..permissions import (
    permission_document_type_create, permission_document_type_delete,
    permission_document_type_edit, permission_document_type_view,
    permission_document_view
)
from ..serializers.document_serializers import DocumentSerializer
from ..serializers.document_type_serializers import (
    DocumentTypeQuickLabelSerializer, DocumentTypeSerializer
)

from .api_view_mixins import ParentObjectDocumentTypeAPIViewMixin

logger = logging.getLogger(name=__name__)


class APIDocumentTypeDocumentListView(
    ExternalObjectAPIViewMixin, generics.ListAPIView
):
    """
    get: Returns a list of all the documents of the selected document types.
    """
    external_object_class = DocumentType
    external_object_pk_url_kwarg = 'document_type_id'
    mayan_external_object_permission_map = {
        'GET': permission_document_type_view
    }
    mayan_object_permission_map = {'GET': permission_document_view}
    serializer_class = DocumentSerializer

    def get_source_queryset(self):
        external_object = self.get_external_object()
        queryset_documents_all = external_object.documents.values('id')
        return Document.valid.filter(pk__in=queryset_documents_all)


class APIDocumentTypeListView(generics.ListCreateAPIView):
    """
    get: Returns a list of all the document types.
    post: Create a new document type.
    """
    mayan_object_permission_map = {'GET': permission_document_type_view}
    mayan_view_permission_map = {'POST': permission_document_type_create}
    serializer_class = DocumentTypeSerializer
    source_queryset = DocumentType.objects.all()

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class APIDocumentTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    delete: Delete the selected document type.
    get: Return the details of the selected document type.
    patch: Edit the properties of the selected document type.
    put: Edit the properties of the selected document type.
    """
    lookup_url_kwarg = 'document_type_id'
    mayan_object_permission_map = {
        'DELETE': permission_document_type_delete,
        'GET': permission_document_type_view,
        'PATCH': permission_document_type_edit,
        'PUT': permission_document_type_edit
    }
    serializer_class = DocumentTypeSerializer
    source_queryset = DocumentType.objects.all()

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class APIDocumentTypeQuickLabelDetailView(
    ParentObjectDocumentTypeAPIViewMixin,
    generics.RetrieveUpdateDestroyAPIView
):
    """
    delete: Delete the selected quick label.
    get: Return the details of the selected quick label.
    patch: Edit the properties of the selected quick label.
    put: Edit the properties of the selected quick label.
    """
    lookup_url_kwarg = 'document_type_quick_label_id'
    mayan_object_permission_map = {
        'DELETE': permission_document_type_edit,
        'GET': permission_document_type_view,
        'PATCH': permission_document_type_edit,
        'PUT': permission_document_type_edit
    }
    serializer_class = DocumentTypeQuickLabelSerializer

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}

    def get_source_queryset(self):
        return self.get_document_type().filenames.all()


class APIDocumentTypeQuickLabelListView(
    ParentObjectDocumentTypeAPIViewMixin, generics.ListCreateAPIView
):
    """
    get: Returns a list of all the document type quick labels.
    post: Create a new document type quick label.
    """
    serializer_class = DocumentTypeQuickLabelSerializer

    def get_instance_extra_data(self):
        return {
            '_event_actor': self.request.user,
            'document_type': self.get_document_type(
                permission=permission_document_type_edit
            )
        }

    def get_source_queryset(self):
        return self.get_document_type(
            permission=permission_document_type_view
        ).filenames.all()
