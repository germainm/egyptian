import logging

from django.apps import apps
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from mayan.apps.document_states.classes import WorkflowAction
from mayan.apps.document_states.exceptions import WorkflowStateActionError

from .exceptions import SequenceError
from .literals import WORKFLOW_ACTION_SEQUENCE_CONTEXT_NAMESPACE
from .models import Sequence
from .permissions import permission_sequence_use
from .validators import validate_sequence_value_store_name

__all__ = ('SequenceValueNextAction',)
logger = logging.getLogger(name=__name__)


class SequenceValueNextAction(WorkflowAction):
    form_field_widgets = {
        'sequence': {
            'class': 'django.forms.widgets.Select', 'kwargs': {
                'attrs': {'class': 'select2'}
            }
        }
    }
    form_fields = {
        'value_store_name': {
            'class': 'django.forms.CharField',
            'help_text': _(
                message='Name of the entry that will hold the value in the '
                'workflow instance context. Later actions and any template '
                'that receives the workflow instance read it as '
                '`{{ workflow_instance_context.sequences.<name> }}`. Leave '
                'this blank to use the internal name of the sequence.'
            ),
            'kwargs': {
                'validators': (validate_sequence_value_store_name,)
            },
            'label': _(message='Value store name'), 'required': False
        }
    }
    label = _(message='Get the next sequence value')
    permission = permission_sequence_use

    @classmethod
    def clean(cls, request, form_data=None, instance=None):
        form_data = form_data or {}

        sequence = cls.get_sequence_for_pk(
            pk=form_data.get('sequence')
        )

        if not sequence:
            return form_data

        value_store_name = form_data.get('value_store_name')

        if value_store_name:
            pass
        else:
            try:
                validate_sequence_value_store_name(sequence.internal_name)
            except ValidationError:
                raise ValidationError(
                    message={
                        'value_store_name': _(
                            message='The internal name of sequence '
                            '"%(sequence)s" cannot be used as a workflow '
                            'context entry. Enter a value store name.'
                        ) % {'sequence': sequence}
                    }
                )

            value_store_name = sequence.internal_name

        cls.do_value_store_name_collision_check(
            instance=instance, value_store_name=value_store_name
        )

        return form_data

    @classmethod
    def do_value_store_name_collision_check(
        cls, value_store_name, instance=None
    ):
        workflow_template_state = getattr(
            cls, 'workflow_template_state', None
        )

        if not workflow_template_state:
            return

        WorkflowStateAction = apps.get_model(
            app_label='document_states', model_name='WorkflowStateAction'
        )

        queryset = WorkflowStateAction.objects.filter(
            backend_path=cls.backend_id,
            state__workflow=workflow_template_state.workflow
        )

        if instance and instance.pk:
            queryset = queryset.exclude(pk=instance.pk)

        for workflow_state_action in queryset:
            backend_instance = workflow_state_action.get_backend_instance()

            sequence = cls.get_sequence_for_pk(
                pk=backend_instance.kwargs.get('sequence')
            )

            if not sequence:
                continue

            other_value_store_name = backend_instance.get_value_store_name(
                sequence=sequence
            )

            if other_value_store_name == value_store_name:
                raise ValidationError(
                    message={
                        'value_store_name': _(
                            message='The workflow action "%(action)s" already '
                            'stores a value under the name "%(name)s". Two '
                            'actions of a workflow cannot share a name; the '
                            'second value would replace the first.'
                        ) % {
                            'action': workflow_state_action,
                            'name': value_store_name
                        }
                    }
                )

    @classmethod
    def get_form_fields(cls):
        fields = super().get_form_fields()

        document_types_queryset = cls.workflow_template_state.workflow.document_types

        sequence_queryset = Sequence.objects.get_for_document_types(
            queryset=document_types_queryset
        )

        fields.update(
            {
                'sequence': {
                    'class': 'mayan.apps.forms.form_fields.FormFieldFilteredModelChoice',
                    'help_text': _(
                        message='Sequence from which the value will be '
                        'consumed. Only sequences enabled for the document '
                        'types of this workflow are shown.'
                    ),
                    'kwargs': {
                        'permission': permission_sequence_use,
                        'source_queryset': sequence_queryset
                    },
                    'label': _(message='Sequence'),
                    'required': True
                }
            }
        )

        return fields

    @classmethod
    def get_form_fieldsets(cls):
        fieldsets = super().get_form_fieldsets()

        fieldsets += (
            (
                _(message='Sequence'), {
                    'fields': ('sequence', 'value_store_name')
                }
            ),
        )

        return fieldsets

    def execute(self, context):
        sequence = self.get_sequence()
        workflow_instance = context['workflow_instance']

        try:
            value = sequence.do_value_next(
                user=self.get_user(context=context)
            )
        except SequenceError as exception:
            raise WorkflowStateActionError(
                _(message='Sequence error: %s') % exception
            ) from exception

        value_store_name = self.get_value_store_name(sequence=sequence)

        logger.debug(
            'Sequence `%s` value `%s` stored as `%s`', sequence.internal_name,
            value, value_store_name
        )

        context_namespace = workflow_instance.loads().get(
            WORKFLOW_ACTION_SEQUENCE_CONTEXT_NAMESPACE, {}
        )
        context_namespace[value_store_name] = value

        workflow_instance.do_context_update(
            context={
                WORKFLOW_ACTION_SEQUENCE_CONTEXT_NAMESPACE: context_namespace
            }
        )

    def get_sequence(self):
        return Sequence.objects.get(
            pk=self.kwargs['sequence']
        )

    @classmethod
    def get_sequence_for_pk(cls, pk):
        if not pk:
            return None

        try:
            return Sequence.objects.get(pk=pk)
        except Sequence.DoesNotExist:
            return None

    def get_user(self, context):
        log_entry = context.get('log_entry')

        return getattr(log_entry, 'user', None)

    def get_value_store_name(self, sequence):
        return self.kwargs.get('value_store_name') or sequence.internal_name
