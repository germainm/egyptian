from django.db import models
from django.utils.translation import gettext_lazy as _

from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import (
    EventManagerMethodAfter, EventManagerSave
)

from ..events import event_workflow_template_edited

from .workflow_models import Workflow
from .workflow_state_model_mixins import (
    WorkflowStateBusinessLogicMixin,
    WorkflowStateRuntimeProxyBusinessLogicMixin
)

__all__ = ('WorkflowState', 'WorkflowStateRuntimeProxy')


class WorkflowState(
    ExtraDataModelMixin, WorkflowStateBusinessLogicMixin, models.Model
):
    _ordering_fields = ('completion', 'final', 'initial', 'label')

    workflow = models.ForeignKey(
        on_delete=models.CASCADE, related_name='states', to=Workflow,
        verbose_name=_(message='Workflow')
    )
    label = models.CharField(
        help_text=_(message='A short text to describe the workflow state.'),
        max_length=255, verbose_name=_(message='Label')
    )
    initial = models.BooleanField(
        default=False,
        help_text=_(
            message='The state at which the workflow will start in. Only one '
            'state can be the initial state.'
        ), verbose_name=_(message='Initial')
    )
    final = models.BooleanField(
        default=False,
        help_text=_(
            message='The state at which the workflow will stop. Only one '
            'state can be the final state.'
        ), verbose_name=_(message='Final')
    )
    completion = models.IntegerField(
        blank=True, default=0, help_text=_(
            message='The percent of completion that this state represents in '
            'relation to the workflow. Use numbers without the percent sign.'
        ), verbose_name=_(message='Completion')
    )

    class Meta:
        ordering = ('label',)
        unique_together = ('workflow', 'label')
        verbose_name = _(message='Workflow state')
        verbose_name_plural = _(message='Workflow states')

    def __str__(self):
        return self.label

    @method_event(
        action_object='self',
        event_manager_class=EventManagerMethodAfter,
        event=event_workflow_template_edited,
        target='workflow'
    )
    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'action_object': 'self',
            'event': event_workflow_template_edited,
            'target': 'workflow'
        },
        edited={
            'action_object': 'self',
            'event': event_workflow_template_edited,
            'target': 'workflow'
        }
    )
    def save(self, *args, **kwargs):

        try:
            self.completion = int(self.completion)
        except (TypeError, ValueError):
            self.completion = 0

        if self.initial:
            self.workflow.states.all().update(initial=False)

        if self.final:
            self.workflow.states.all().update(final=False)

        return super().save(*args, **kwargs)


class WorkflowStateRuntimeProxy(
    WorkflowStateRuntimeProxyBusinessLogicMixin, WorkflowState
):
    class Meta:
        proxy = True
        verbose_name = _(message='Workflow state runtime proxy')
        verbose_name_plural = _(message='Workflow state runtime proxies')
