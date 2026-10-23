from rest_framework.generics import get_object_or_404

from mayan.apps.acls.models import AccessControlList
from mayan.apps.documents.models.document_models import Document
from mayan.apps.documents.permissions import permission_document_view
from mayan.apps.rest_api import generics

from .models import FavoriteDocument
from .serializers import FavoriteDocumentSerializer


class APIFavoriteDocumentDetailView(generics.RetrieveDestroyAPIView):
    """
    delete: Delete the selected favorite document.
    get: Return the details of the selected favorite document.
    """
    lookup_url_kwarg = 'favorite_document_id'
    mayan_object_permission_map = {
        'DELETE': permission_document_view,
        'GET': permission_document_view
    }
    serializer_class = FavoriteDocumentSerializer

    def get_source_queryset(self):
        return FavoriteDocument.valid.filter(user=self.request.user)


class APIFavoriteDocumentListView(generics.ListCreateAPIView):
    """
    get: Return a list of the favorite documents for the current user.
    post: Add a new document to the list of favorite documents for the current user.
    """
    mayan_object_permission_map = {'GET': permission_document_view}
    serializer_class = FavoriteDocumentSerializer

    def get_instance_extra_data(self):
        return {'user': self.request.user}

    def get_source_queryset(self):
        return FavoriteDocument.valid.filter(user=self.request.user)

    def perform_create(self, serializer):
        queryset = Document.valid.all()

        queryset = AccessControlList.objects.restrict_queryset(
            permission=permission_document_view, queryset=queryset,
            user=self.request.user
        )

        serializer.validated_data['document'] = get_object_or_404(
            queryset=queryset, pk=serializer.validated_data['document_id']
        )
        super().perform_create(serializer=serializer)
