from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.serializers.document_type_serializers import (
    DocumentTypeSerializer
)
from mayan.apps.rest_api import serializers
from mayan.apps.rest_api.relations import MultiKwargHyperlinkedIdentityField

from ..models import DocumentTypeDriverConfiguration

from .file_metadata_serializers import StoredDriverSerializer


class DocumentTypeDriverConfigurationSerializer(serializers.ModelSerializer):
    document_type = DocumentTypeSerializer(
        label=_(message='Document type'), read_only=True
    )
    stored_driver = StoredDriverSerializer(
        label=_(message='Stored driver'), read_only=True
    )
    url = MultiKwargHyperlinkedIdentityField(
        label=_(message='URL'), view_kwargs=(
            {
                'lookup_field': 'document_type_id',
                'lookup_url_kwarg': 'document_type_id'
            },
            {
                'lookup_field': 'pk',
                'lookup_url_kwarg': 'driver_id'
            }
        ), view_name='rest_api:document_type_file_metadata_configuration-detail'
    )

    class Meta:
        fields = (
            'arguments', 'document_type', 'enabled', 'id', 'stored_driver',
            'url'
        )
        model = DocumentTypeDriverConfiguration
        read_only_fields = ('document_type', 'id', 'stored_driver', 'url')
