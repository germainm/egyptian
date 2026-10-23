from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.validators import YAMLValidator
from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import EventManagerSave

from ..events import event_metadata_type_created, event_metadata_type_edited
from ..managers import MetadataTypeManager

from .metadata_type_model_mixins import MetadataTypeBusinessLogicMixin


class MetadataType(
    ExtraDataModelMixin, MetadataTypeBusinessLogicMixin, models.Model
):
    _ordering_fields = ('label', 'name')

    name = models.CharField(
        max_length=48,
        help_text=_(
            message='Name used by other apps to reference this metadata '
            'type. Do not use python reserved words, or spaces.'
        ),
        unique=True, verbose_name=_(message='Name')
    )
    label = models.CharField(
        help_text=_(message='Short description of this metadata type.'),
        max_length=48, verbose_name=_(message='Label')
    )
    default = models.CharField(
        blank=True, max_length=128, null=True, help_text=_(
            message='Enter a template to render.'
        ), verbose_name=_(message='Default')
    )
    lookup = models.TextField(
        blank=True, null=True, help_text=_(
            message='Enter a template to render. Must result in a comma '
            'delimited string.'
        ), verbose_name=_(message='Lookup')
    )
    validation = models.CharField(
        blank=True, help_text=_(
            message='The validator will reject data entry if the value '
            'entered does not conform to the expected format.'
        ), max_length=224, verbose_name=_(message='Validator')
    )
    validation_arguments = models.TextField(
        blank=True, help_text=_(
            message='Enter the arguments for the validator in YAML format.'
        ), validators=[YAMLValidator()], verbose_name=_(
            message='Validator arguments'
        )
    )
    parser = models.CharField(
        blank=True, help_text=_(
            message='The parser will reformat the value entered to conform '
            'to the expected format.'
        ), max_length=224, verbose_name=_(message='Parser')
    )
    parser_arguments = models.TextField(
        blank=True, help_text=_(
            message='Enter the arguments for the parser in YAML format.'
        ), validators=[
            YAMLValidator()
        ], verbose_name=_(message='Parser arguments')
    )

    objects = MetadataTypeManager()

    class Meta:
        ordering = ('label',)
        verbose_name = _(message='Metadata type')
        verbose_name_plural = _(message='Metadata types')

    def __str__(self):
        return self.label

    def get_absolute_url(self):
        return reverse(
            kwargs={'metadata_type_id': self.pk},
            viewname='metadata:metadata_type_edit'
        )

    def natural_key(self):
        return (self.name,)

    @method_event(
        created={
            'event': event_metadata_type_created,
            'target': 'self',
        },
        edited={
            'event': event_metadata_type_edited,
            'target': 'self',
        },
        event_manager_class=EventManagerSave
    )
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)

    def validate_value(self, document_type, value):
        if not value and self.default:
            value = self.get_default_value()

        if not value and self.get_required_for(document_type=document_type):
            raise ValidationError(
                message=_(
                    message='"%s" is required for this document type.'
                ) % self.label
            )

        if self.lookup:
            lookup_options = self.get_lookup_values()

            if value and value not in lookup_options:
                raise ValidationError(
                    message=_(
                        message='Value is not one of the provided options.'
                    )
                )

        if self.validation:
            validator = self.get_validator_instance()
            try:
                validator.validate(value)
            except ValidationError as exception:
                raise ValidationError(
                    message=_(
                        message='Metadata type validation error; '
                        '%(exception)s'
                    ) % {
                        'exception': ','.join(exception)
                    }
                ) from exception

        if self.parser:
            parser = self.get_parser_instance()
            value = parser.parse(value)

        return value
