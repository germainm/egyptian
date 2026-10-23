import logging

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from mayan.apps.acls.models import AccessControlList
from mayan.apps.rest_api import generics

from ..classes import DocumentFileAction
from ..models.document_models import Document
from ..models.document_type_models import DocumentType
from ..permissions import (
    permission_document_change_type, permission_document_create,
    permission_document_properties_edit, permission_document_trash,
    permission_document_view
)
from ..serializers.document_serializers import (
    DocumentFileActionSerializer, DocumentSerializer,
    DocumentChangeTypeSerializer, DocumentUploadSerializer
)
from ..tasks.document_tasks import task_document_move_to_trash

logger = logging.getLogger(name=__name__)


class APIDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Returns the selected document details.
    delete: Move the selected document to the thrash.
    get: Return the details of the selected document.
    patch: Edit the properties of the selected document.
    put: Edit the properties of the selected document.
    """
    lookup_url_kwarg = 'document_id'
    mayan_object_permission_map = {
        'DELETE': permission_document_trash,
        'GET': permission_document_view,
        'PATCH': permission_document_properties_edit,
        'PUT': permission_document_properties_edit
    }
    serializer_class = DocumentSerializer
    source_queryset = Document.valid.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        task_document_move_to_trash.apply_async(
            kwargs={
                'document_id': instance.pk, 'user_id': self.request.user.pk
            }
        )

        return Response(status=status.HTTP_202_ACCEPTED)

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class APIDocumentFileActionListView(generics.ListAPIView):
    """
    get: Returns a list of the available document file actions.
    """
    serializer_class = DocumentFileActionSerializer

    def get_serializer_context(self):
        return {
            'format': self.format_kwarg,
            'request': self.request,
            'view': self
        }

    def get_source_queryset(self):
        return DocumentFileAction.get_all()


class APIDocumentListView(generics.ListCreateAPIView):
    """
    get: Returns a list of all the documents.
    post: Create a new document.
    """
    mayan_object_permission_map = {'GET': permission_document_view}
    serializer_class = DocumentSerializer
    source_queryset = Document.valid.all()

    def perform_create(self, serializer):
        queryset = DocumentType.objects.all()

        queryset = AccessControlList.objects.restrict_queryset(
            permission=permission_document_create, queryset=queryset,
            user=self.request.user
        )

        serializer.validated_data['document_type'] = get_object_or_404(
            pk=serializer.validated_data['document_type_id'],
            queryset=queryset
        )
        super().perform_create(serializer=serializer)

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class APIDocumentChangeTypeView(generics.ObjectActionAPIView):
    """
    post: Change the type of the selected document.
    """
    lookup_url_kwarg = 'document_id'
    mayan_object_permission_map = {'POST': permission_document_change_type}
    serializer_class = DocumentChangeTypeSerializer
    source_queryset = Document.valid.all()

    def object_action(self, obj, request, serializer):
        document_type_id = serializer.validated_data['document_type_id']
        obj.document_type_change(
            document_type=document_type_id, user=self.request.user
        )


DOCUMENT_UPLOAD_API_VIEW_SUNSET = 'Thu, 01 Jul 2027 00:00:00 GMT'
DOCUMENT_UPLOAD_API_VIEW_DEPRECATION_LINK = 'https://docs.mayan-edms.com/'


@extend_schema_view(
    post=extend_schema(deprecated=True)
)
class APIDocumentUploadView(generics.CreateAPIView):
    """
    post: Create a new document and a new document file. Deprecated: use the
    sources app action execute endpoint (POST
    /sources/{source_id}/actions/{action_name}/execute/) as the canonical
    document capture entry point. This endpoint is scheduled for removal in
    Mayan EDMS 5.0.
    """
    serializer_class = DocumentUploadSerializer

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(
            request, response, *args, **kwargs
        )
        response['Deprecation'] = 'true'
        response['Sunset'] = DOCUMENT_UPLOAD_API_VIEW_SUNSET
        link_header = '<{}>; rel="deprecation"; type="text/html"'.format(
            DOCUMENT_UPLOAD_API_VIEW_DEPRECATION_LINK
        )
        response['Link'] = link_header
        return response

    def perform_create(self, serializer):
        queryset = DocumentType.objects.all()

        queryset = AccessControlList.objects.restrict_queryset(
            permission=permission_document_create, queryset=queryset,
            user=self.request.user
        )

        serializer.validated_data['document_type'] = get_object_or_404(
            pk=serializer.validated_data['document_type_id'],
            queryset=queryset
        )
        super().perform_create(serializer=serializer)

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}
