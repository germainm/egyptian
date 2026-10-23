from django.db import models
from django.utils.translation import gettext_lazy as _

from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.documents.models.document_type_models import DocumentType
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import (
    EventManagerMethodAfter, EventManagerSave
)

from .events import event_smart_link_created, event_smart_link_edited
from .literals import INCLUSION_AND, INCLUSION_CHOICES, OPERATOR_CHOICES
from .managers import SmartLinkManager
from .model_mixins import (
    ResolvedSmartLinkBusinessLogicMixin, SmartLinkBusinessLogicMixin,
    SmartLinkConditionBusinessLogicMixin
)


class SmartLink(
    ExtraDataModelMixin, SmartLinkBusinessLogicMixin, models.Model
):
    _ordering_fields = ('dynamic_label', 'enabled', 'label')

    label = models.CharField(
        db_index=True, help_text=_(
            message='A short text describing the smart link.'
        ), max_length=128, verbose_name=_(message='Label')
    )
    dynamic_label = models.CharField(
        blank=True, max_length=96, help_text=_(
            message='Use this field to show a unique label depending on the '
            'document from which the smart link is being accessed.'
        ), verbose_name=_(message='Dynamic label')
    )
    enabled = models.BooleanField(
        default=True, verbose_name=_(message='Enabled')
    )
    document_types = models.ManyToManyField(
        related_name='smart_links', to=DocumentType,
        verbose_name=_(message='Document types')
    )

    objects = SmartLinkManager()

    class Meta:
        ordering = ('label',)
        verbose_name = _(message='Smart link')
        verbose_name_plural = _(message='Smart links')

    def __str__(self):
        return self.label

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'event': event_smart_link_created,
            'target': 'self'
        },
        edited={
            'event': event_smart_link_edited,
            'target': 'self'
        }
    )
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class ResolvedSmartLink(ResolvedSmartLinkBusinessLogicMixin, SmartLink):
    class Meta:
        proxy = True


class SmartLinkCondition(
    ExtraDataModelMixin, SmartLinkConditionBusinessLogicMixin, models.Model
):
    _ordering_fields = ('enabled',)

    smart_link = models.ForeignKey(
        on_delete=models.CASCADE, related_name='conditions', to=SmartLink,
        verbose_name=_(message='Smart link')
    )
    inclusion = models.CharField(
        choices=INCLUSION_CHOICES, default=INCLUSION_AND,
        help_text=_(message='The inclusion is ignored for the first item.'),
        max_length=16, verbose_name=_(message='Inclusion')
    )
    foreign_document_data = models.CharField(
        help_text=_(
            message='This represents the metadata of all other documents.'
        ), max_length=128, verbose_name=_(
            message='Foreign document attribute'
        )
    )
    operator = models.CharField(
        choices=OPERATOR_CHOICES, max_length=16,
        verbose_name=_(message='Operator')
    )
    expression = models.TextField(
        help_text=_(
            message='The expression using document properties to be '
            'evaluated against the foreign document field.'
        ), verbose_name=_(message='Expression')
    )
    negated = models.BooleanField(
        default=False, help_text=_(
            message='Inverts the logic of the operator.'
        ), verbose_name=_(message='Negated')
    )
    enabled = models.BooleanField(
        default=True, verbose_name=_(message='Enabled')
    )

    class Meta:
        verbose_name = _(message='Link condition')
        verbose_name_plural = _(message='Link conditions')

    def __str__(self):
        return self.get_full_label()

    @method_event(
        event_manager_class=EventManagerMethodAfter,
        event=event_smart_link_edited,
        target='smart_link'
    )
    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'action_object': 'self',
            'event': event_smart_link_edited,
            'target': 'smart_link'
        },
        edited={
            'action_object': 'self',
            'event': event_smart_link_edited,
            'target': 'smart_link'
        }
    )
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)
