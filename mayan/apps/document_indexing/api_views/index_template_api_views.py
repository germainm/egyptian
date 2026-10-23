from mayan.apps.documents.permissions import permission_document_type_view
from mayan.apps.documents.serializers.document_type_serializers import (
    DocumentTypeSerializer
)
from mayan.apps.rest_api import generics
from mayan.apps.rest_api.api_view_mixins import ExternalObjectAPIViewMixin

from ..models.index_template_models import IndexTemplate
from ..permissions import (
    permission_index_template_create, permission_index_template_delete,
    permission_index_template_edit, permission_index_template_rebuild,
    permission_index_template_view
)
from ..serializers.index_template_serializers import (
    DocumentTypeAddSerializer, DocumentTypeRemoveSerializer,
    IndexTemplateSerializer
)
from ..tasks import task_index_template_rebuild

from .index_template_api_view_mixins import APIIndexTemplateNodeViewMixin


class APIIndexTemplateListView(generics.ListCreateAPIView):
    """
    get: Returns a list of all the defined indexes template.
    post: Create a new index template.
    """
    mayan_object_permission_map = {'GET': permission_index_template_view}
    mayan_view_permission_map = {'POST': permission_index_template_create}
    serializer_class = IndexTemplateSerializer
    source_queryset = IndexTemplate.objects.all()

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class APIIndexTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    delete: Delete the selected index template.
    get: Returns the details of the selected index template.
    patch: Partially edit an index template.
    put: Edit an index template.
    """
    lookup_url_kwarg = 'index_template_id'
    mayan_object_permission_map = {
        'DELETE': permission_index_template_delete,
        'GET': permission_index_template_view,
        'PATCH': permission_index_template_edit,
        'PUT': permission_index_template_edit
    }
    serializer_class = IndexTemplateSerializer
    source_queryset = IndexTemplate.objects.all()

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class APIIndexTemplateDocumentTypeListView(
    ExternalObjectAPIViewMixin, generics.ListAPIView
):
    """
    get: Returns a list of the document types associated with this index template.
    """
    external_object_class = IndexTemplate
    external_object_pk_url_kwarg = 'index_template_id'
    mayan_external_object_permission_map = {
        'GET': permission_index_template_view
    }
    mayan_object_permission_map = {'GET': permission_document_type_view}
    serializer_class = DocumentTypeSerializer

    def get_source_queryset(self):
        return self.get_external_object().document_types.all()


class APIIndexTemplateDocumentTypeAddView(generics.ObjectActionAPIView):
    """
    post: Add a document type to an index template.
    """
    lookup_url_kwarg = 'index_template_id'
    mayan_object_permission_map = {'POST': permission_index_template_edit}
    serializer_class = DocumentTypeAddSerializer
    source_queryset = IndexTemplate.objects.all()

    def object_action(self, obj, request, serializer):
        document_type = serializer.validated_data['document_type']
        obj.document_types_add(
            queryset=[document_type], user=self.request.user
        )


class APIIndexTemplateDocumentTypeRemoveView(generics.ObjectActionAPIView):
    """
    post: Remove a document type from an index template.
    """
    lookup_url_kwarg = 'index_template_id'
    mayan_object_permission_map = {'POST': permission_index_template_edit}
    serializer_class = DocumentTypeRemoveSerializer
    source_queryset = IndexTemplate.objects.all()

    def object_action(self, obj, request, serializer):
        document_type = serializer.validated_data['document_type']
        obj.document_types_remove(
            queryset=[document_type], user=self.request.user
        )


class APIIndexTemplateNodeListView(
    APIIndexTemplateNodeViewMixin, generics.ListCreateAPIView
):
    """
    get: Returns a list of all the template nodes for the selected index.
    post: Create a new index template node.
    """
    def get_source_queryset(self):
        return self.get_index_template().index_template_root_node.get_children()


class APIIndexTemplateNodeDetailView(
    APIIndexTemplateNodeViewMixin, generics.RetrieveUpdateDestroyAPIView
):
    """
    delete: Delete the selected index template node.
    get: Returns the details of the selected index template node.
    patch: Partially edit an index template node.
    put: Edit an index template node.
    """
    lookup_url_kwarg = 'index_template_node_id'

    def get_source_queryset(self):
        return self.get_index_template().index_template_nodes.exclude(
            parent=None
        )


class APIIndexTemplateRebuildView(generics.ObjectActionAPIView):
    """
    post: Rebuild the selected index template.
    """
    lookup_url_kwarg = 'index_template_id'
    mayan_object_permission_map = {
        'POST': permission_index_template_rebuild
    }
    source_queryset = IndexTemplate.objects.all()

    def object_action(self, obj, request, serializer):
        task_index_template_rebuild.apply_async(
            kwargs={
                'index_id': obj.pk
            }
        )


class APIIndexTemplateResetView(generics.ObjectActionAPIView):
    """
    post: Reset the selected index template.
    """
    lookup_url_kwarg = 'index_template_id'
    mayan_object_permission_map = {
        'POST': permission_index_template_rebuild
    }
    source_queryset = IndexTemplate.objects.all()

    def object_action(self, obj, request, serializer):
        obj.reset()
