from django.apps import apps
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from mayan.apps.events.classes import EventType


class WorkflowManager(models.Manager):
    def get_queryset_auto_launch(self, document_type):
        queryset = self.filter(
            auto_launch=True, document_types=document_type
        )

        return queryset

    def launch_for(self, document, user=None):
        queryset_workflow_templates = self.get_queryset_auto_launch(
            document_type=document.document_type
        )

        for workflow_template in queryset_workflow_templates:
            workflow_template.launch_for(document=document, user=user)


class WorkflowTransitionTriggerEventManager(models.Manager):
    def check_triggers(self, action):
        Document = apps.get_model(
            app_label='documents', model_name='Document'
        )
        WorkflowInstance = apps.get_model(
            app_label='document_states', model_name='WorkflowInstance'
        )
        StoredEventType = apps.get_model(
            app_label='events', model_name='StoredEventType'
        )
        WorkflowTransition = apps.get_model(
            app_label='document_states', model_name='WorkflowTransition'
        )

        stored_event_type_id = StoredEventType.objects.get_pk_for_name(
            name=action.verb
        )

        if stored_event_type_id is None:
            return

        queryset_trigger_events = self.filter(
            event_type_id=stored_event_type_id
        )

        queryset_trigger_events = queryset_trigger_events.order_by()

        transition_id_list = list(
            queryset_trigger_events.values_list('transition_id', flat=True)
        )

        if not transition_id_list:
            return

        queryset_triggered_transitions = WorkflowTransition.objects.filter(
            pk__in=transition_id_list
        )

        if isinstance(action.target, Document):
            queryset_workflow_instances = WorkflowInstance.objects.filter(
                workflow__transitions__in=queryset_triggered_transitions,
                document=action.target
            ).distinct()
        elif isinstance(action.action_object, Document):
            queryset_workflow_instances = WorkflowInstance.objects.filter(
                workflow__transitions__in=queryset_triggered_transitions,
                document=action.action_object
            ).distinct()
        else:
            queryset_workflow_instances = WorkflowInstance.objects.none()

        queryset_workflow_instances = queryset_workflow_instances.exclude(
            Q(workflow__ignore_completed=True) & Q(state_active__final=True)
        )

        for workflow_instance in queryset_workflow_instances:
            queryset_valid_transitions = queryset_triggered_transitions & workflow_instance.get_queryset_valid_transitions()

            if queryset_valid_transitions.exists():
                event_type_label = EventType.get_label(id=action.verb)

                workflow_instance.do_transition(
                    comment=_(message='Event trigger: %s') % event_type_label,
                    transition=queryset_valid_transitions.first()
                )


class ValidWorkflowInstanceManager(models.Manager):
    def get_queryset(self):
        return models.QuerySet(
            model=self.model, using=self._db
        ).filter(document__in_trash=False)
