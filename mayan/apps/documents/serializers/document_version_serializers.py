from django.utils.translation import gettext_lazy as _

from mayan.apps.common.serializers import ContentTypeSerializer
from mayan.apps.converter.relations import ImageURLField
from mayan.apps.rest_api import serializers
from mayan.apps.rest_api.relations import MultiKwargHyperlinkedIdentityField

from ..classes import DocumentVersionModification
from ..models.document_version_models import DocumentVersion
from ..models.document_version_page_models import DocumentVersionPage


class DocumentVersionModificationSerializer(serializers.Serializer):
    id = serializers.CharField(
        label=_(message='ID'), read_only=True, source='backend_class_path'
    )
    label = serializers.CharField(
        label=_(message='Label'), read_only=True
    )
    description = serializers.CharField(
        label=_(message='Description'), read_only=True
    )


class DocumentVersionModificationExecuteSerializer(serializers.Serializer):
    backend_id = serializers.ChoiceField(
        choices=(), label=_(message='Backend ID'), help_text=_(
            message='Primary key of the modification backend to execute.'
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['backend_id'].choices = DocumentVersionModification.get_choices()


class DocumentVersionPageSerializer(serializers.HyperlinkedModelSerializer):
    content_type = ContentTypeSerializer(
        label=_(message='Content type'), read_only=True
    )
    content_type_id = serializers.IntegerField(
        help_text=_(message='Content type ID of the source object for the page.'),
        write_only=True
    )
    document_version_url = MultiKwargHyperlinkedIdentityField(
        label=_(message='Document version URL'), view_kwargs=(
            {
                'lookup_field': 'document_version.document.pk',
                'lookup_url_kwarg': 'document_id'
            },
            {
                'lookup_field': 'document_version_id',
                'lookup_url_kwarg': 'document_version_id'
            }
        ), view_name='rest_api:documentversion-detail'
    )
    image_url = ImageURLField(
        label=_(message='Image URL'), view_kwargs=(
            {
                'lookup_field': 'document_version.document.pk',
                'lookup_url_kwarg': 'document_id'
            },
            {
                'lookup_field': 'document_version_id',
                'lookup_url_kwarg': 'document_version_id'
            },
            {
                'lookup_field': 'pk',
                'lookup_url_kwarg': 'document_version_page_id'
            }
        ), view_name='rest_api:documentversionpage-image'
    )
    url = MultiKwargHyperlinkedIdentityField(
        label=_(message='URL'), view_kwargs=(
            {
                'lookup_field': 'document_version.document.pk',
                'lookup_url_kwarg': 'document_id'
            },
            {
                'lookup_field': 'document_version_id',
                'lookup_url_kwarg': 'document_version_id'
            },
            {
                'lookup_field': 'pk',
                'lookup_url_kwarg': 'document_version_page_id'
            }
        ), view_name='rest_api:documentversionpage-detail'
    )

    class Meta:
        fields = (
            'content_type', 'content_type_id', 'document_version_id',
            'document_version_url', 'id', 'image_url', 'object_id',
            'page_number', 'url'
        )
        model = DocumentVersionPage
        read_only_fields = (
            'content_type', 'document_version_id', 'document_version_url',
            'id', 'image_url', 'url'
        )


class DocumentVersionSerializer(serializers.HyperlinkedModelSerializer):
    document_url = serializers.HyperlinkedIdentityField(
        label=_(message='Document URL'), lookup_field='document_id',
        lookup_url_kwarg='document_id', view_name='rest_api:document-detail'
    )
    export_url = MultiKwargHyperlinkedIdentityField(
        label=_(message='Export URL'), view_kwargs=(
            {
                'lookup_field': 'document_id',
                'lookup_url_kwarg': 'document_id'
            },
            {
                'lookup_field': 'pk',
                'lookup_url_kwarg': 'document_version_id'
            }
        ), view_name='rest_api:documentversion-export'
    )
    page_list_url = MultiKwargHyperlinkedIdentityField(
        label=_(message='Page list URL'), view_kwargs=(
            {
                'lookup_field': 'document_id',
                'lookup_url_kwarg': 'document_id'
            },
            {
                'lookup_field': 'pk',
                'lookup_url_kwarg': 'document_version_id'
            }
        ), view_name='rest_api:documentversionpage-list'
    )
    pages_first = DocumentVersionPageSerializer(
        label=_(message='Pages first'), many=False, read_only=True
    )
    url = MultiKwargHyperlinkedIdentityField(
        label=_(message='URL'), view_kwargs=(
            {
                'lookup_field': 'document_id',
                'lookup_url_kwarg': 'document_id'
            },
            {
                'lookup_field': 'pk',
                'lookup_url_kwarg': 'document_version_id'
            }
        ), view_name='rest_api:documentversion-detail'
    )

    class Meta:
        fields = (
            'active', 'comment', 'document_id', 'document_url', 'export_url',
            'id', 'page_list_url', 'pages_first', 'timestamp', 'url'
        )
        model = DocumentVersion
        read_only_fields = (
            'document_id', 'document_url', 'export_url', 'id',
            'page_list_url', 'pages_first', 'timestamp', 'url'
        )
