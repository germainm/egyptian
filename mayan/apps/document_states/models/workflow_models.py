from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.validators import validate_internal_name
from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.documents.models.document_type_models import DocumentType
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import EventManagerSave

from ..events import (
    event_workflow_template_created, event_workflow_template_edited
)
from ..managers import WorkflowManager

from .workflow_model_mixins import (
    WorkflowBusinessLogicMixin, WorkflowRuntimeProxyBusinessLogicMixin
)

__all__ = ('Workflow', 'WorkflowRuntimeProxy')


class Workflow(
    ExtraDataModelMixin, WorkflowBusinessLogicMixin, models.Model
):
    _ordering_fields = (
        'internal_name', 'label', 'auto_launch', 'ignore_completed'
    )

    auto_launch = models.BooleanField(
        default=True, help_text=_(
            message='Launch workflow when document is created.'
        ), verbose_name=_(message='Auto launch')
    )
    internal_name = models.CharField(
        db_index=True, help_text=_(
            message='This value will be used by other apps to reference this '
            'workflow. Can only contain letters, numbers, and underscores.'
        ), max_length=255, unique=True, validators=[validate_internal_name],
        verbose_name=_(message='Internal name')
    )
    label = models.CharField(
        help_text=_(message='A short text to describe the workflow.'),
        max_length=255, unique=True, verbose_name=_(message='Label')
    )
    document_types = models.ManyToManyField(
        related_name='workflows', to=DocumentType, verbose_name=_(
            message='Document types'
        )
    )
    ignore_completed = models.BooleanField(
        default=False, help_text=_(
            message='Ignore workflow instances if they are in their final '
            'state.'
        ), verbose_name=_(message='Ignore completed')
    )

    objects = WorkflowManager()

    class Meta:
        ordering = ('label',)
        verbose_name = _(message='Workflow')
        verbose_name_plural = _(message='Workflows')

    def __str__(self):
        return self.label

    def get_absolute_url(self):
        return reverse(viewname='document_states:workflow_template_list')

    def delete(self, *args, **kwargs):
        self.cache_partition.delete()
        return super().delete(*args, **kwargs)

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'event': event_workflow_template_created,
            'target': 'self'
        },
        edited={
            'event': event_workflow_template_edited,
            'target': 'self'
        }
    )
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class WorkflowRuntimeProxy(WorkflowRuntimeProxyBusinessLogicMixin, Workflow):
    class Meta:
        proxy = True
        verbose_name = _(message='Workflow runtime proxy')
        verbose_name_plural = _(message='Workflow runtime proxies')
