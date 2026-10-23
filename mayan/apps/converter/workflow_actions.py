import logging

from django.utils.translation import gettext_lazy as _

from mayan.apps.common.utils import parse_range
from mayan.apps.common.validators import RangeValidator
from mayan.apps.document_states.classes import WorkflowAction
from mayan.apps.document_states.models.workflow_instance_models import (
    WorkflowInstance
)
from mayan.apps.templating.template_backends import Template

from .models import ObjectLayer
from .transformations import BaseTransformation

__all__ = ('TransformationAddAction',)
logger = logging.getLogger(name=__name__)


class TransformationAddAction(WorkflowAction):
    form_field_widgets = {
        'transformation_class': {
            'class': 'django.forms.widgets.Select', 'kwargs': {
                'attrs': {'class': 'select2'}
            }
        }
    }
    form_fields = {
        'pages': {
            'label': _(message='Pages'),
            'class': 'django.forms.CharField', 'kwargs': {
                'help_text': _(
                    message='Pages to which the new transformations will be '
                    'added. Separate by commas and/or use a dashes for a '
                    'ranges. Leave blank to select all pages.'
                ), 'required': False, 'validators': (
                    RangeValidator(),
                )
            }
        },
        'transformation_class': {
            'label': _(message='Transformation class'),
            'class': 'django.forms.ChoiceField', 'kwargs': {
                'choices': BaseTransformation.get_transformation_choices(
                    group_by_layer=True
                ), 'help_text': _(
                    message='Type of transformation to add.'
                ), 'required': True
            }
        },
        'transformation_arguments': {
            'label': _(message='Transformation arguments'),
            'class': 'mayan.apps.templating.fields.ModelTemplateField',
            'kwargs': {
                'initial_help_text': _(
                    message='Enter a template that will generate the '
                    'arguments for the transformation as a '
                    'YAML dictionary. ie: {"degrees": 180}. The document '
                    'version page is available as '
                    '{{ document_version_page }}.'
                ), 'model': WorkflowInstance,
                'model_variable': 'workflow_instance', 'required': False
            }
        }
    }
    label = _(message='Add transformation')

    @classmethod
    def get_form_fieldsets(cls):
        fieldsets = super().get_form_fieldsets()

        fieldsets += (
            (
                _(message='Objects'), {
                    'fields': ('pages',)
                }
            ),
            (
                _(message='Transformations'), {
                    'fields': (
                        'transformation_class', 'transformation_arguments',
                    )
                }
            ),
        )
        return fieldsets

    def execute(self, context):
        if self.kwargs['pages']:
            page_range = parse_range(
                range_string=self.kwargs['pages']
            )
            queryset = context['workflow_instance'].document.pages.filter(
                page_number__in=page_range
            )
        else:
            queryset = context['workflow_instance'].document.pages.all()

        transformation_class = BaseTransformation.get(
            name=self.kwargs['transformation_class']
        )
        layer = transformation_class.get_assigned_layer()

        template = Template(
            template_string=self.kwargs['transformation_arguments']
        )

        for document_page in queryset.all():
            context['document_version_page'] = document_page

            template_result = template.render(context=context)

            object_layer, created = ObjectLayer.objects.get_for(
                layer=layer, obj=document_page
            )
            object_layer.transformations.create(
                arguments=template_result, name=transformation_class.name
            )
