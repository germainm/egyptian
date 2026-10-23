from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from .models import Sequence
from .settings import setting_value_count_maximum


class SequenceSerializer(serializers.HyperlinkedModelSerializer):
    next_value = serializers.CharField(
        help_text=_(
            message='Value that the next use of this sequence will return. '
            'Reading this field does not consume the value.'
        ), read_only=True, source='get_value_preview'
    )
    position_remaining = serializers.SerializerMethodField(
        help_text=_(
            message='Positions left before the sequence is exhausted. Null '
            'when the backend is unbounded.'
        )
    )
    value_next_url = serializers.HyperlinkedIdentityField(
        lookup_url_kwarg='sequence_id',
        view_name='rest_api:sequence-value-next'
    )

    class Meta:
        extra_kwargs = {
            'value_is_unique': {'read_only': True},
            'url': {
                'lookup_url_kwarg': 'sequence_id',
                'view_name': 'rest_api:sequence-detail'
            }
        }
        fields = (
            'backend_data', 'backend_path', 'id', 'internal_name', 'label',
            'next_value', 'on_limit', 'position', 'position_remaining',
            'url', 'value_is_unique', 'value_next_url'
        )
        model = Sequence

    def get_position_remaining(self, instance):
        return instance.get_position_remaining()


class SequenceValueNextSerializer(serializers.Serializer):
    count = serializers.IntegerField(
        default=1, help_text=_(
            message='How many values to consume in one call. The block is '
            'reserved atomically.'
        ), min_value=1, required=False
    )
    value_list = serializers.ListField(
        child=serializers.CharField(), read_only=True
    )

    def validate_count(self, value):
        value_count_maximum = setting_value_count_maximum.value

        if value > value_count_maximum:
            message = _(
                message='The number of requested values cannot be greater '
                'than %(value_count_maximum)s.'
            ) % {'value_count_maximum': value_count_maximum}
            raise serializers.ValidationError(message)

        return value
