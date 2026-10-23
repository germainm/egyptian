from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.events.classes import EventType
from mayan.apps.events.models import StoredEventType
from mayan.apps.views.generics import FormView
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from ..forms.workflow_template_transition_trigger_forms import (
    WorkflowTransitionTriggerEventRelationshipFormSet
)
from ..icons import icon_workflow_template_transition_triggers
from ..models import WorkflowTransition
from ..permissions import permission_workflow_template_view


class WorkflowTemplateTransitionTriggerEventListView(
    ExternalObjectViewMixin, FormView
):
    external_object_class = WorkflowTransition
    external_object_permission = permission_workflow_template_view
    external_object_pk_url_kwarg = 'workflow_template_transition_id'
    form_class = WorkflowTransitionTriggerEventRelationshipFormSet
    view_icon = icon_workflow_template_transition_triggers

    def form_valid(self, form):
        try:
            for instance in form:
                instance.save()
        except Exception as exception:
            messages.error(
                message=_(
                    message='Error updating workflow transition trigger '
                    'events; %s'
                ) % exception, request=self.request

            )
        else:
            messages.success(
                message=_(
                    message='Workflow transition trigger events updated '
                    'successfully'
                ), request=self.request
            )

        return super().form_valid(form=form)

    def get_extra_context(self):
        return {
            'form_display_mode_table': True,
            'navigation_object_list': ('object', 'workflow'),
            'object': self.external_object,
            'subtitle': _(
                message='Triggers are events that cause this transition to '
                'execute automatically.'
            ),
            'submit_label': _(message='Save'),
            'title': _(
                message='Workflow transition trigger events for: %s'
            ) % self.external_object,
            'workflow': self.external_object.workflow
        }

    def get_initial(self):
        obj = self.external_object
        initial = []

        event_type_ids = [
            event_type.id for event_type in EventType.all()
        ]
        queryset_event_types = StoredEventType.objects.filter(
            name__in=event_type_ids
        )

        queryset_event_types = sorted(
            queryset_event_types, key=lambda x: (x.namespace, x.label)
        )

        for event_type in queryset_event_types:
            initial.append(
                {
                    'event_type': event_type,
                    'transition': obj
                }
            )
        return initial

    def get_post_action_redirect(self):
        return reverse(
            kwargs={'workflow_template_id': self.external_object.workflow.pk},
            viewname='document_states:workflow_template_transition_list'
        )
