from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import ValidationError

from mayan.apps.events.classes import EventType
from mayan.apps.events.serializers.event_type_serializers import (
    EventTypeSerializer
)
from mayan.apps.rest_api import serializers
from mayan.apps.rest_api.relations import MultiKwargHyperlinkedIdentityField

from ..models.workflow_transition_trigger_models import (
    WorkflowTransitionTriggerEvent
)


class WorkflowTemplateTransitionTriggerSerializer(
    serializers.HyperlinkedModelSerializer
):
    event_type = EventTypeSerializer(
        label=_(message='Event type'), read_only=True
    )
    event_type_id = serializers.CharField(
        label=_(message='Event Type ID'), source='event_type.event_type.id',
        write_only=True
    )
    url = MultiKwargHyperlinkedIdentityField(
        label=_(message='URL'), view_kwargs=(
            {
                'lookup_field': 'transition.workflow_id',
                'lookup_url_kwarg': 'workflow_template_id'
            },
            {
                'lookup_field': 'transition_id',
                'lookup_url_kwarg': 'workflow_template_transition_id'
            },
            {
                'lookup_field': 'pk',
                'lookup_url_kwarg': 'workflow_template_transition_trigger_id'
            }
        ), view_name='rest_api:workflow-template-transition-trigger-detail'
    )
    workflow_template_url = MultiKwargHyperlinkedIdentityField(
        label=_(message='Workflow template URL'), view_kwargs=(
            {
                'lookup_field': 'transition__workflow_id',
                'lookup_url_kwarg': 'workflow_template_id'
            },
        ), view_name='rest_api:workflow-template-detail'
    )
    workflow_transition_id = serializers.IntegerField(
        label=_(message='Workflow transition ID'), read_only=True,
        source='transition_id'
    )
    workflow_transition_url = MultiKwargHyperlinkedIdentityField(
        label=_(message='Workflow transition URL'), view_kwargs=(
            {
                'lookup_field': 'transition.workflow_id',
                'lookup_url_kwarg': 'workflow_template_id'
            },
            {
                'lookup_field': 'transition_id',
                'lookup_url_kwarg': 'workflow_template_transition_id'
            }
        ), view_name='rest_api:workflow-template-transition-detail'
    )

    class Meta:
        fields = (
            'event_type', 'event_type_id', 'id', 'url',
            'workflow_template_url', 'workflow_transition_id',
            'workflow_transition_url'
        )
        model = WorkflowTransitionTriggerEvent
        read_only_fields = (
            'id', 'url', 'workflow_template_url', 'workflow_transition_id',
            'workflow_transition_url'
        )

    def create(self, validated_data):
        event_type = validated_data.pop('event_type', None)
        event_type = event_type.get(
            'event_type', {}
        )
        event_type_id = event_type.get('id')

        if event_type_id:
            validated_data['event_type'] = EventType.get(
                id=event_type_id
            ).get_stored_event_type()

        return super().create(validated_data=validated_data)

    def update(self, instance, validated_data):
        event_type = validated_data.pop('event_type', None)
        event_type = event_type.get(
            'event_type', {}
        )
        event_type_id = event_type.get('id')

        if event_type_id:
            validated_data['event_type'] = EventType.get(
                id=event_type_id
            ).get_stored_event_type()

        return super().update(
            instance=instance, validated_data=validated_data
        )

    def validate_event_type_id(self, data):
        try:
            EventType.get(id=data)
        except KeyError:
            raise ValidationError(
                message=_(
                    message='Unknown or invalid event type ID `%s`'
                ) % data
            )
        else:
            return data
