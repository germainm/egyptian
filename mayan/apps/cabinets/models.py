from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import connection, models, transaction
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.documents.models.document_models import Document
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import (
    EventManagerMethodAfter, EventManagerSave
)

from .events import (
    event_cabinet_created, event_cabinet_deleted,
    event_cabinet_document_added, event_cabinet_document_removed,
    event_cabinet_edited
)
from .model_mixins import CabinetBusinessLogicMixin


class Cabinet(CabinetBusinessLogicMixin, ExtraDataModelMixin, MPTTModel):
    _ordering_fields = ('label',)

    parent = TreeForeignKey(
        blank=True, db_index=True, null=True, on_delete=models.CASCADE,
        related_name='children', to='self', verbose_name=_(message='Parent')
    )
    label = models.CharField(
        help_text=_(message='A short text used to identify the cabinet.'),
        max_length=128, verbose_name=_(message='Label')
    )
    documents = models.ManyToManyField(
        blank=True, related_name='cabinets', to=Document,
        verbose_name=_(message='Documents')
    )

    class MPTTMeta:
        order_insertion_by = ('label',)

    class Meta:
        unique_together = ('parent', 'label')
        verbose_name = _(message='Cabinet')
        verbose_name_plural = _(message='Cabinets')

    def __str__(self):
        return self.get_full_path()

    @method_event(
        action_object='self',
        event=event_cabinet_document_added,
        event_manager_class=EventManagerMethodAfter
    )
    def _document_add(self, document, user=None):
        self._event_actor = user
        self._event_target = document
        self.documents.add(document)

    @method_event(
        action_object='self',
        event=event_cabinet_document_removed,
        event_manager_class=EventManagerMethodAfter
    )
    def _document_remove(self, document, user=None):
        self._event_actor = user
        self._event_target = document
        self.documents.remove(document)

    @method_event(
        action_object='parent',
        event=event_cabinet_deleted,
        event_manager_class=EventManagerMethodAfter
    )
    def delete(self, *args, **kwargs):
        self._event_actor = getattr(self, '_event_actor', 'parent')

        result = super().delete(*args, **kwargs)

        if not self.parent:
            self._event_ignore = True

        return result

    def get_absolute_url(self):
        return reverse(
            kwargs={'cabinet_id': self.pk},
            viewname='cabinets:cabinet_view'
        )

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'action_object': 'parent',
            'event': event_cabinet_created,
            'target': 'self'
        },
        edited={
            'event': event_cabinet_edited,
            'target': 'self'
        }
    )
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)

    def validate_unique(self, exclude=None):
        with transaction.atomic():
            if connection.vendor == 'oracle':
                queryset = Cabinet.objects.filter(
                    parent=self.parent, label=self.label
                )
            else:
                queryset = Cabinet.objects.select_for_update().filter(
                    parent=self.parent, label=self.label
                )

            if queryset.exists():
                params = {
                    'field_labels': _(message='Parent and Label'),
                    'model_name': _(message='Cabinet')
                }
                raise ValidationError(
                    message={
                        NON_FIELD_ERRORS: [
                            ValidationError(
                                message=_(
                                    message='%(model_name)s with this '
                                    '%(field_labels)s already exists.'
                                ), code='unique_together', params=params
                            )
                        ]
                    }
                )


class CabinetSearchResult(Cabinet):
    class Meta:
        proxy = True
        verbose_name = _(message='Cabinet')
        verbose_name_plural = _(message='Cabinets')


class DocumentCabinet(Cabinet):
    class Meta:
        proxy = True
        verbose_name = _(message='Document cabinet')
        verbose_name_plural = _(message='Document cabinets')
