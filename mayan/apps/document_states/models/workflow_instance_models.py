from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.documents.models.document_models import Document
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import EventManagerSave

from ..events import (
    event_workflow_instance_created, event_workflow_instance_transitioned
)
from ..managers import ValidWorkflowInstanceManager

from .workflow_instance_model_mixins import (
    WorkflowInstanceBusinessLogicMixin,
    WorkflowInstanceLogEntryBusinessLogicMixin
)
from .workflow_models import Workflow
from .workflow_state_models import WorkflowState
from .workflow_transition_field_models import WorkflowTransitionField

__all__ = ('WorkflowInstance', 'WorkflowInstanceLogEntry')


class WorkflowInstance(
    ExtraDataModelMixin, WorkflowInstanceBusinessLogicMixin, models.Model
):
    _ordering_fields = ('datetime',)

    workflow = models.ForeignKey(
        help_text=_(message='The workflow template.'),
        on_delete=models.CASCADE,
        related_name='instances', to=Workflow,
        verbose_name=_(message='Workflow')
    )
    datetime = models.DateTimeField(
        auto_now_add=True, db_index=True,
        help_text=_(message='Workflow instance creation date time.'),
        verbose_name=_(message='Datetime')
    )
    document = models.ForeignKey(
        help_text=_(
            message='The document to which the workflow instance is '
            'attached.'
        ), on_delete=models.CASCADE, related_name='workflows', to=Document,
        verbose_name=_(message='Document')
    )
    context = models.TextField(
        blank=True, verbose_name=_(message='Context')
    )
    state_active = models.ForeignKey(
        help_text=_(
            message='The currently active state of the workflow instance.'
        ),
        on_delete=models.CASCADE, related_name='workflow_instances',
        to=WorkflowState, verbose_name=_(message='Active state')
    )

    objects = models.Manager()
    valid = ValidWorkflowInstanceManager()

    class Meta:
        ordering = ('workflow',)
        unique_together = ('document', 'workflow')
        verbose_name = _(message='Workflow instance')
        verbose_name_plural = _(message='Workflow instances')

    def __str__(self):
        return str(self.workflow)

    def get_absolute_url(self):
        return reverse(
            viewname='document_states:workflow_instance_detail', kwargs={
                'workflow_instance_id': self.pk
            }
        )

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'action_object': 'document',
            'event': event_workflow_instance_created,
            'target': 'self'
        }
    )
    def save(self, *args, **kwargs):
        created = not self.pk

        if created:
            self.state_active = self.workflow.get_state_initial()

        super().save(*args, **kwargs)


class WorkflowInstanceLogEntry(
    WorkflowInstanceLogEntryBusinessLogicMixin, models.Model
):
    _ordering_fields = ('comment', 'datetime')

    workflow_instance = models.ForeignKey(
        on_delete=models.CASCADE, related_name='log_entries',
        to=WorkflowInstance, verbose_name=_(message='Workflow instance')
    )
    datetime = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name=_(message='Datetime')
    )
    transition = models.ForeignKey(
        blank=True, null=True, on_delete=models.CASCADE,
        to='WorkflowTransition', verbose_name=_(message='Transition')
    )
    user = models.ForeignKey(
        blank=True, null=True, on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL, verbose_name=_(message='User')
    )
    comment = models.TextField(
        blank=True, verbose_name=_(message='Comment')
    )
    extra_data = models.TextField(
        blank=True, verbose_name=_(message='Extra data')
    )

    class Meta:
        ordering = ('datetime',)
        verbose_name = _(message='Workflow instance log entry')
        verbose_name_plural = _(message='Workflow instance log entries')

    def __str__(self):
        if self.transition:
            return str(self.transition)
        else:
            return str(
                _(message='Initial state')
            )

    def clean(self):
        queryset = self.workflow_instance.get_queryset_valid_transitions(
            user=self.user
        )
        if not queryset.filter(pk=self.transition.pk).exists():
            raise ValidationError(
                message=_(message='Not a valid transition choice.')
            )

        extra_data = self.loads()

        for field_name, value in extra_data.items():
            try:
                field = self.transition.fields.get(name=field_name)
            except WorkflowTransitionField.DoesNotExist:
                """
                Allow extra data keys that do not match to a know field
                to allow backward compatibility. This may change in the
                future.
                Possible deprecation.
                """
            else:
                field.validate_value(value=value, workflow_instance=self)

    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)

        if self.transition:
            actor = getattr(self, '_event_actor', None)
            event_workflow_instance_transitioned.commit(
                action_object=self.workflow_instance.document, actor=actor,
                target=self.workflow_instance
            )

            self.transition.origin_state.do_active_unset(log_entry=self)
            self.transition.destination_state.do_active_set(log_entry=self)
        else:
            self.workflow_instance.state_active.do_active_set(log_entry=self)

        return result
