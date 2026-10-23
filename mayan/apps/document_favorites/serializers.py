from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.serializers.document_serializers import (
    DocumentSerializer
)
from mayan.apps.rest_api import serializers
from mayan.apps.user_management.serializers import UserSerializer

from .models import FavoriteDocument


class FavoriteDocumentSerializer(serializers.HyperlinkedModelSerializer):
    document = DocumentSerializer(
        label=_(message='Document'), read_only=True
    )
    document_id = serializers.IntegerField(
        help_text=_(message='Document ID for the new favorite document.'),
        label=_(message='Document ID'), write_only=True
    )
    user = UserSerializer(
        label=_(message='User'), read_only=True
    )

    class Meta:
        extra_kwargs = {
            'url': {
                'label': _(message='URL'),
                'lookup_url_kwarg': 'favorite_document_id',
                'view_name': 'rest_api:favoritedocument-detail'
            }
        }
        fields = (
            'document', 'document_id', 'datetime_added', 'id', 'user', 'url'
        )
        model = FavoriteDocument
        read_only_fields = (
            'document', 'datetime_added', 'id', 'user', 'url'
        )
