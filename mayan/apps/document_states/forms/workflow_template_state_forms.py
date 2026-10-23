import json

from django.utils.translation import gettext_lazy as _

from mayan.apps.backends.forms import FormDynamicModelBackend
from mayan.apps.forms import form_fields, form_widgets, forms
from mayan.apps.templating.fields import ModelTemplateField

from ..classes import WorkflowAction
from ..models import (
    WorkflowInstance, WorkflowState, WorkflowStateAction,
    WorkflowStateEscalation
)


class WorkflowTemplateStateActionDynamicForm(FormDynamicModelBackend):
    class Meta:
        fields = ('label', 'when', 'enabled', 'condition', 'backend_data')
        model = WorkflowStateAction
        widgets = {'backend_data': form_widgets.HiddenInput}

    def __init__(self, backend_class, request, user=None, *args, **kwargs):
        self.backend_class = backend_class
        self.request = request
        self.user = user
        result = super().__init__(*args, **kwargs)

        self.fields['condition'] = ModelTemplateField(
            initial_help_text=self.fields['condition'].help_text,
            label=self.fields['condition'].label, model=WorkflowInstance,
            model_variable='workflow_instance', required=False
        )

        return result

    def clean(self):
        data = super().clean()

        if self.errors:
            return data

        backend_data = json.loads(
            s=data['backend_data']
        )

        self.backend_class.clean(
            form_data=backend_data, instance=self.instance,
            request=self.request
        )

        return data


class WorkflowTemplateStateActionSelectionForm(forms.Form):
    klass = form_fields.ChoiceField(
        choices=(), help_text=_(
            message='The action type for this action entry.'
        ), label=_(message='Action'), widget=form_widgets.Select(
            attrs={'class': 'select2'}
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['klass'].choices = WorkflowAction.get_choices()


class WorkflowTemplateStateEscalationForm(forms.ModelForm):
    def __init__(self, workflow_template_state, *args, **kwargs):
        self.workflow_template_state = workflow_template_state
        super().__init__(*args, **kwargs)

        queryset_transitions = self.workflow_template_state.workflow.transitions.filter(
            origin_state=self.workflow_template_state
        )

        self.fields['transition'].queryset = queryset_transitions

        self.fields['condition'] = ModelTemplateField(
            initial_help_text=self.fields['condition'].help_text,
            label=self.fields['condition'].label, model=WorkflowInstance,
            model_variable='workflow_instance', required=False
        )

    class Meta:
        fields = (
            'enabled', 'transition', 'priority', 'unit', 'amount',
            'condition'
        )
        model = WorkflowStateEscalation


class WorkflowTemplateStateForm(forms.ModelForm):
    class Meta:
        fields = ('initial', 'final', 'label', 'completion')
        model = WorkflowState
