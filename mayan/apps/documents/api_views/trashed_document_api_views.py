import logging

from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from mayan.apps.converter.api_view_mixins import APIImageViewMixin
from mayan.apps.rest_api import generics

from ..models.trashed_document_models import TrashedDocument
from ..permissions import (
    permission_document_version_view, permission_document_view,
    permission_trashed_document_delete, permission_trashed_document_restore
)
from ..serializers.trashed_document_serializers import (
    TrashedDocumentSerializer
)
from ..tasks import task_trashed_document_delete

logger = logging.getLogger(name=__name__)


class APITrashedDocumentDetailView(generics.RetrieveDestroyAPIView):
    """
    Returns the selected trashed document details.
    delete: Delete the trashed document.
    get: Retrieve the details of the trashed document.
    """
    lookup_url_kwarg = 'document_id'
    mayan_object_permission_map = {
        'DELETE': permission_trashed_document_delete,
        'GET': permission_document_view
    }
    serializer_class = TrashedDocumentSerializer
    source_queryset = TrashedDocument.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        task_trashed_document_delete.apply_async(
            kwargs={
                'trashed_document_id': instance.pk,
                'user_id': self.request.user.pk
            }
        )

        return Response(status=status.HTTP_202_ACCEPTED)


class APITrashedDocumentListView(generics.ListAPIView):
    """
    get: Returns a list of all the trashed documents.
    """
    mayan_object_permission_map = {'GET': permission_document_view}
    serializer_class = TrashedDocumentSerializer
    source_queryset = TrashedDocument.objects.all()


class APITrashedDocumentRestoreView(generics.ObjectActionAPIView):
    """
    post: Restore a trashed document.
    """
    lookup_url_kwarg = 'document_id'
    mayan_object_permission_map = {
        'POST': permission_trashed_document_restore
    }
    source_queryset = TrashedDocument.objects.all()

    def object_action(self, obj, request, serializer):
        obj.restore(user=self.request.user)


class APITrashedDocumentImageView(
    APIImageViewMixin, generics.RetrieveAPIView
):
    """
    get: Returns an image representation of the selected trashed document.
    """
    lookup_url_kwarg = 'document_id'
    mayan_object_permission_map = {'GET': permission_document_version_view}

    def get_object(self):
        obj = super().get_object()

        first_page = obj.pages.first()

        if first_page:
            first_page_id = first_page.pk
        else:
            first_page_id = None

        return get_object_or_404(queryset=obj.pages, pk=first_page_id)

    def get_source_queryset(self):
        return TrashedDocument.objects.all()
