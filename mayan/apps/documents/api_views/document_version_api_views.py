import logging

from rest_framework import status

from mayan.apps.converter.api_view_mixins import APIImageViewMixin
from mayan.apps.rest_api import generics

from ..classes import DocumentVersionModification
from ..permissions import (
    permission_document_version_create, permission_document_version_delete,
    permission_document_version_edit, permission_document_version_view
)
from ..serializers.document_version_serializers import (
    DocumentVersionModificationSerializer,
    DocumentVersionModificationExecuteSerializer, DocumentVersionSerializer,
    DocumentVersionPageSerializer
)

from .api_view_mixins import (
    ParentObjectDocumentAPIViewMixin, ParentObjectDocumentVersionAPIViewMixin
)

logger = logging.getLogger(name=__name__)


class APIDocumentVersionDetailView(
    ParentObjectDocumentAPIViewMixin, generics.RetrieveUpdateDestroyAPIView
):
    """
    delete: Delete the selected document version.
    get: Returns the selected document version details.
    patch: Edit the properties of the selected document version.
    put: Edit the properties of the selected document version.
    """
    lookup_url_kwarg = 'document_version_id'
    mayan_object_permission_map = {
        'DELETE': permission_document_version_delete,
        'GET': permission_document_version_view,
        'PATCH': permission_document_version_edit,
        'PUT': permission_document_version_edit
    }
    serializer_class = DocumentVersionSerializer

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}

    def get_source_queryset(self):
        document = self.get_document()
        return document.versions.all()


class APIDocumentVersionListView(
    ParentObjectDocumentAPIViewMixin, generics.ListCreateAPIView
):
    """
    get: Return a list of the selected document's versions.
    post: Create a new document version.
    """
    mayan_object_permission_map = {
        'GET': permission_document_version_view,
    }
    serializer_class = DocumentVersionSerializer

    def get_instance_extra_data(self):
        return {
            '_event_actor': self.request.user,
            'document': self.get_document(
                permission=permission_document_version_create
            )
        }

    def get_source_queryset(self):
        document = self.get_document()
        return document.versions.all()


class APIDocumentVersionModificationView(
    ParentObjectDocumentAPIViewMixin, generics.ObjectActionAPIView
):
    """
    post: Execute a modification backend on the selected document version.
    """
    action_response_status = status.HTTP_202_ACCEPTED
    lookup_url_kwarg = 'document_version_id'
    mayan_object_permission_map = {'POST': permission_document_version_edit}
    serializer_class = DocumentVersionModificationExecuteSerializer

    def get_source_queryset(self):
        document = self.get_document()
        return document.versions.all()

    def object_action(self, obj, request, serializer):
        document_version_modification = DocumentVersionModification.get(
            name=serializer.validated_data['backend_id']
        )

        document_version_modification.execute(
            document_version=obj, user=request.user
        )


class APIDocumentVersionModificationBackendListView(generics.ListAPIView):
    """
    get: Returns a list of the available document version modification backends.
    """
    serializer_class = DocumentVersionModificationSerializer

    def get_serializer_context(self):
        return {
            'format': self.format_kwarg,
            'request': self.request,
            'view': self
        }

    def get_source_queryset(self):
        return DocumentVersionModification.get_all()


class APIDocumentVersionPageDetailView(
    ParentObjectDocumentVersionAPIViewMixin,
    generics.RetrieveUpdateDestroyAPIView
):
    """
    delete: Delete the selected document version page.
    get: Returns the selected document version page details.
    patch: Edit the properties of the selected document version page.
    put: Edit the properties of the selected document version page.
    """
    lookup_url_kwarg = 'document_version_page_id'
    mayan_object_permission_map = {
        'DELETE': permission_document_version_edit,
        'GET': permission_document_version_view,
        'PATCH': permission_document_version_edit,
        'PUT': permission_document_version_edit
    }
    serializer_class = DocumentVersionPageSerializer

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}

    def get_source_queryset(self):
        document_version = self.get_document_version()
        return document_version.pages.all()


class APIDocumentVersionPageImageView(
    APIImageViewMixin, ParentObjectDocumentVersionAPIViewMixin,
    generics.RetrieveAPIView
):
    """
    get: Returns an image representation of the selected document version page.
    """
    lookup_url_kwarg = 'document_version_page_id'
    mayan_object_permission_map = {'GET': permission_document_version_view}

    def get_source_queryset(self):
        document_version = self.get_document_version()
        return document_version.pages.all()


class APIDocumentVersionPageListView(
    ParentObjectDocumentVersionAPIViewMixin, generics.ListCreateAPIView
):
    """
    get: Returns an list of the pages for the selected document version.
    post: Create a new document version page.
    """
    lookup_url_kwarg = 'document_version_page_id'
    serializer_class = DocumentVersionPageSerializer

    def get_instance_extra_data(self):
        return {
            '_event_actor': self.request.user,
            'document_version': self.get_document_version(
                permission=permission_document_version_edit
            )
        }

    def get_source_queryset(self):
        document_version = self.get_document_version(
            permission=permission_document_version_view
        )
        return document_version.pages.all()
