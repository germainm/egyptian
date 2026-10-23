from django.utils.translation import gettext_lazy as _

from rest_framework.reverse import reverse

from mayan.apps.documents.models.document_type_models import DocumentType
from mayan.apps.documents.permissions import permission_document_type_edit
from mayan.apps.documents.serializers.document_serializers import (
    DocumentSerializer
)
from mayan.apps.rest_api import serializers
from mayan.apps.rest_api.relations import (
    FilteredPrimaryKeyRelatedField, MultiKwargHyperlinkedIdentityField
)

from .models import ResolvedSmartLink, SmartLink, SmartLinkCondition


class SmartLinkConditionSerializer(serializers.HyperlinkedModelSerializer):
    smart_link_url = serializers.HyperlinkedIdentityField(
        label=_(message='Smart link URL'), lookup_url_kwarg='smart_link_id',
        view_name='rest_api:smartlink-detail'
    )
    url = MultiKwargHyperlinkedIdentityField(
        label=_(message='URL'), view_kwargs=(
            {
                'lookup_field': 'smart_link_id',
                'lookup_url_kwarg': 'smart_link_id'
            },
            {
                'lookup_field': 'pk',
                'lookup_url_kwarg': 'smart_link_condition_id'
            }
        ), view_name='rest_api:smartlinkcondition-detail'
    )

    class Meta:
        fields = (
            'enabled', 'expression', 'foreign_document_data', 'inclusion',
            'id', 'negated', 'operator', 'smart_link_id', 'smart_link_url',
            'url'
        )
        model = SmartLinkCondition
        read_only_fields = ('id', 'smart_link_id', 'smart_link_url', 'url')


class SmartLinkDocumentTypeAddSerializer(serializers.Serializer):
    document_type = FilteredPrimaryKeyRelatedField(
        help_text=_(
            message='Primary key of the document type to add to the smart '
            'link.'
        ), label=_(message='Document type ID'), source_model=DocumentType,
        source_permission=permission_document_type_edit
    )


class SmartLinkDocumentTypeRemoveSerializer(serializers.Serializer):
    document_type = FilteredPrimaryKeyRelatedField(
        help_text=_(
            message='Primary key of the document type to remove from the '
            'smart link.'
        ), label=_(message='Document type ID'), source_model=DocumentType,
        source_permission=permission_document_type_edit
    )


class SmartLinkSerializer(serializers.HyperlinkedModelSerializer):
    conditions_url = serializers.HyperlinkedIdentityField(
        label=_(message='Conditions URL'), lookup_url_kwarg='smart_link_id',
        view_name='rest_api:smartlinkcondition-list'
    )
    document_types_url = serializers.HyperlinkedIdentityField(
        label=_(message='Document types URL'),
        lookup_url_kwarg='smart_link_id',
        view_name='rest_api:smartlink-document_type-list'
    )
    document_types_add_url = serializers.HyperlinkedIdentityField(
        label=_(message='Document types add URL'),
        lookup_url_kwarg='smart_link_id',
        view_name='rest_api:smartlink-document_type-add'
    )
    document_types_remove_url = serializers.HyperlinkedIdentityField(
        label=_(message='Document types remove URL'),
        lookup_url_kwarg='smart_link_id',
        view_name='rest_api:smartlink-document_type-remove'
    )

    class Meta:
        extra_kwargs = {
            'url': {
                'label': _(message='URL'),
                'lookup_url_kwarg': 'smart_link_id',
                'view_name': 'rest_api:smartlink-detail'
            }
        }
        fields = (
            'conditions_url', 'document_types_url', 'document_types_add_url',
            'document_types_remove_url', 'dynamic_label', 'enabled',
            'label', 'id', 'url'
        )
        model = SmartLink
        read_only_fields = (
            'conditions_url', 'document_types_url', 'document_types_add_url',
            'document_types_remove_url', 'id', 'url'
        )


class ResolvedSmartLinkDocumentSerializer(DocumentSerializer):
    resolved_smart_link_url = serializers.SerializerMethodField(
        label=_(message='Resolved smart link URL')
    )

    class Meta(DocumentSerializer.Meta):
        fields = DocumentSerializer.Meta.fields + (
            'resolved_smart_link_url',
        )
        read_only_fields = DocumentSerializer.Meta.fields

    def get_resolved_smart_link_url(self, instance):
        return reverse(
            format=self.context['format'], kwargs={
                'document_id': self.context['document'].pk,
                'resolved_smart_link_id': self.context['resolved_smart_link'].pk
            }, request=self.context['request'],
            viewname='rest_api:resolvedsmartlink-detail'
        )


class ResolvedSmartLinkSerializer(serializers.HyperlinkedModelSerializer):
    documents_url = serializers.SerializerMethodField(
        label=_(message='Documents URL')
    )
    label = serializers.SerializerMethodField(
        label=_(message='Label')
    )
    smart_link_url = serializers.SerializerMethodField(
        label=_(message='Smart link URL')
    )
    url = serializers.SerializerMethodField(
        label=_(message='URL')
    )

    class Meta:
        fields = (
            'documents_url', 'id', 'label', 'smart_link_url', 'url'
        )
        model = ResolvedSmartLink
        read_only_fields = fields

    def get_documents_url(self, instance):
        return reverse(
            format=self.context['format'], kwargs={
                'document_id': self.context['document'].pk,
                'resolved_smart_link_id': instance.pk
            },
            request=self.context['request'],
            viewname='rest_api:resolvedsmartlinkdocument-list'
        )

    def get_label(self, instance):
        return instance.get_label_for(
            document=self.context['document']
        )

    def get_smart_link_url(self, instance):
        return reverse(
            format=self.context['format'], kwargs={
                'smart_link_id': instance.pk
            }, request=self.context['request'],
            viewname='rest_api:smartlink-detail'
        )

    def get_url(self, instance):
        return reverse(
            format=self.context['format'], kwargs={
                'document_id': self.context['document'].pk,
                'resolved_smart_link_id': instance.pk
            },
            request=self.context['request'],
            viewname='rest_api:resolvedsmartlink-detail'
        )
