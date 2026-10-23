from rest_framework import status
from rest_framework.response import Response

from mayan.apps.converter.api_view_mixins import APIImageViewMixin
from mayan.apps.rest_api import generics
from mayan.apps.storage.models import SharedUploadedFile

from ..permissions import (
    permission_document_file_delete, permission_document_file_edit,
    permission_document_file_new, permission_document_file_view
)
from ..serializers.document_file_serializers import (
    DocumentFileSerializer, DocumentFilePageSerializer
)
from ..tasks import task_document_file_delete, task_document_file_upload

from .api_view_mixins import (
    ParentObjectDocumentAPIViewMixin, ParentObjectDocumentFileAPIViewMixin
)


class APIDocumentFileListView(
    ParentObjectDocumentAPIViewMixin, generics.ListCreateAPIView
):
    """
    get: Return a list of the selected document's files.
    post: Create a new document file.
    """
    serializer_class = DocumentFileSerializer
    mayan_object_permission_map = {
        'GET': permission_document_file_view,
    }

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(status=status.HTTP_202_ACCEPTED)

    def perform_create(self, serializer):
        shared_uploaded_file = SharedUploadedFile.objects.create(
            file=serializer.validated_data['file_new']
        )

        task_document_file_upload.apply_async(
            kwargs={
                'action_name': serializer.validated_data['action_name'],
                'comment': serializer.validated_data.get('comment', ''),
                'document_id': self.get_document(
                    permission=permission_document_file_new
                ).pk,
                'filename': serializer.validated_data.get('filename', ''),
                'shared_uploaded_file_id': shared_uploaded_file.pk,
                'user_id': self.request.user.pk
            }
        )

    def get_source_queryset(self):
        document = self.get_document()
        return document.files.all()


class APIDocumentFileDetailView(
    ParentObjectDocumentAPIViewMixin, generics.RetrieveUpdateDestroyAPIView
):
    """
    delete: Delete the selected document file.
    get: Returns the selected document file details.
    """
    lookup_url_kwarg = 'document_file_id'
    mayan_object_permission_map = {
        'DELETE': permission_document_file_delete,
        'GET': permission_document_file_view,
        'PATCH': permission_document_file_edit,
        'PUT': permission_document_file_edit
    }
    serializer_class = DocumentFileSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        task_document_file_delete.apply_async(
            kwargs={
                'document_file_id': instance.pk,
                'user_id': request.user.pk
            }
        )
        return Response(status=status.HTTP_202_ACCEPTED)

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}

    def get_source_queryset(self):
        document = self.get_document()
        return document.files.all()




class APIDocumentFilePageDetailView(
    ParentObjectDocumentFileAPIViewMixin, generics.RetrieveAPIView
):
    """
    get: Returns the selected document page details.
    """
    lookup_url_kwarg = 'document_file_page_id'
    mayan_object_permission_map = {'GET': permission_document_file_view}
    serializer_class = DocumentFilePageSerializer

    def get_source_queryset(self):
        document_file = self.get_document_file()
        return document_file.pages.all()


class APIDocumentFilePageImageView(
    APIImageViewMixin, ParentObjectDocumentFileAPIViewMixin,
    generics.RetrieveAPIView
):
    """
    get: Returns an image representation of the selected document.
    """
    lookup_url_kwarg = 'document_file_page_id'
    mayan_object_permission_map = {'GET': permission_document_file_view}

    def get_source_queryset(self):
        document_file = self.get_document_file()
        return document_file.pages.all()


class APIDocumentFilePageListView(
    ParentObjectDocumentFileAPIViewMixin, generics.ListAPIView
):
    serializer_class = DocumentFilePageSerializer

    def get_source_queryset(self):
        document_file = self.get_document_file(
            permission=permission_document_file_view
        )
        return document_file.pages.all()
