from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.permissions import permission_document_view
from mayan.apps.documents.search import search_model_document
from mayan.apps.dynamic_search.search_models import SearchModel

from .permissions import permission_metadata_type_view


search_model_document.add_model_field(
    field='metadata__metadata_type__name', label=_(message='Metadata type')
)
search_model_document.add_model_field(
    field='metadata__value', label=_(message='Metadata value')
)


search_model_document_metadata = SearchModel(
    app_label='metadata', label=_(message='Document metadata'),
    model_name='DocumentMetadataSearchResult',
    permission=permission_document_view,
    serializer_path='mayan.apps.metadata.serializers.DocumentMetadataSerializer'
)

search_model_document_metadata.add_proxy_model(
    app_label='metadata', model_name='DocumentMetadata'
)

search_model_document_metadata.add_model_field(
    field='document__document_type__id',
    label=_(message='Document type ID')
)
search_model_document_metadata.add_model_field(
    field='document__document_type__label',
    label=_(message='Document type label')
)
search_model_document_metadata.add_model_field(
    field='metadata_type__id', label=_(message='Metadata type ID')
)
search_model_document_metadata.add_model_field(field='metadata_type__name')
search_model_document_metadata.add_model_field(field='value')


search_model_metadata_type = SearchModel(
    app_label='metadata', model_name='MetadataType',
    permission=permission_metadata_type_view,
    serializer_path='mayan.apps.metadata.serializers.MetadataTypeSerializer'
)

search_model_metadata_type.add_model_field(field='default')
search_model_metadata_type.add_model_field(field='label')
search_model_metadata_type.add_model_field(field='lookup')
search_model_metadata_type.add_model_field(field='name')
search_model_metadata_type.add_model_field(field='parser')
search_model_metadata_type.add_model_field(field='validation')
