from django.db import models
from django.utils.translation import gettext_lazy as _

from mayan.apps.backends.model_mixins import BackendModelMixin
from mayan.apps.common.validators import validate_internal_name
from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.documents.models.document_type_models import DocumentType
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import EventManagerSave

from .classes import SequenceBackendNull
from .events import event_sequence_created, event_sequence_edited
from .literals import ON_LIMIT_CHOICES, ON_LIMIT_RAISE
from .managers import SequenceManager
from .model_mixins import SequenceBusinessLogicMixin


class Sequence(
    SequenceBusinessLogicMixin, BackendModelMixin, ExtraDataModelMixin,
    models.Model
):
    _backend_model_null_backend = SequenceBackendNull
    _ordering_fields = ('label', 'internal_name')

    label = models.CharField(
        help_text=_(message='Short description of this sequence.'),
        max_length=128, unique=True, verbose_name=_(message='Label')
    )
    internal_name = models.CharField(
        db_index=True, help_text=_(
            message='This value will be used by other apps to reference '
            'this sequence. Can only contain letters, numbers, and '
            'underscores.'
        ), max_length=255, unique=True, validators=[validate_internal_name],
        verbose_name=_(message='Internal name')
    )
    position = models.BigIntegerField(
        db_index=True, default=0, help_text=_(
            message='Zero based counter of how many values have been '
            'consumed. Set this to continue the numbering of a system '
            'being replaced.'
        ), verbose_name=_(message='Position')
    )
    value_is_unique = models.BooleanField(
        default=True, editable=False, help_text=_(
            message='Whether a value of this sequence identifies a single '
            'position. Recorded when the sequence is saved and not entered '
            'by hand.'
        ), null=True, verbose_name=_(message='Values are unique')
    )
    on_limit = models.CharField(
        choices=ON_LIMIT_CHOICES, default=ON_LIMIT_RAISE, help_text=_(
            message='What to do when the sequence reaches the last '
            'position its backend is able to represent.'
        ), max_length=16, verbose_name=_(message='On limit')
    )
    document_types = models.ManyToManyField(
        blank=True, help_text=_(
            message='Document types that are allowed to use this sequence. '
            'Associating more than one document type is supported and '
            'means those document types draw from the same pool of '
            'values.'
        ), related_name='sequences', to=DocumentType,
        verbose_name=_(message='Document types')
    )

    objects = SequenceManager()

    class Meta:
        ordering = ('label',)
        verbose_name = _(message='Sequence')
        verbose_name_plural = _(message='Sequences')

    def __str__(self):
        return self.label

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'event': event_sequence_created,
            'target': 'self'
        },
        edited={
            'event': event_sequence_edited,
            'target': 'self'
        }
    )
    def save(self, *args, **kwargs):
        update_field_list = kwargs.get('update_fields') or ()

        if not update_field_list or 'backend_data' in update_field_list:
            self.value_is_unique = self.get_value_is_unique()

        return super().save(*args, **kwargs)
