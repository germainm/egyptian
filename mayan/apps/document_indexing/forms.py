from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.models.document_models import Document
from mayan.apps.forms import form_fields, form_widgets, forms, formsets
from mayan.apps.templating.fields import ModelTemplateField

from .literals import RELATIONSHIP_CHOICES
from .models.index_template_models import IndexTemplate, IndexTemplateNode
from .permissions import permission_index_template_rebuild


class IndexTemplateEventTriggerRelationshipForm(forms.Form):
    stored_event_type_id = form_fields.IntegerField(
        widget=form_widgets.HiddenInput()
    )
    namespace = form_fields.CharField(
        label=_(message='Namespace'), required=False, widget=form_widgets.TextInput(
            attrs={'readonly': 'readonly'}
        )
    )
    label = form_fields.CharField(
        label=_(message='Label'), required=False, widget=form_widgets.TextInput(
            attrs={'readonly': 'readonly'}
        )
    )
    relationship = form_fields.ChoiceField(
        choices=RELATIONSHIP_CHOICES, label=_(message='Enabled'),
        widget=form_widgets.RadioSelect()
    )


IndexTemplateEventTriggerRelationshipFormSet = formsets.formset_factory(
    form=IndexTemplateEventTriggerRelationshipForm, extra=0
)


class IndexTemplateFilteredForm(forms.FilteredSelectionForm):
    class Meta:
        allow_multiple = True
        field_name = 'index_templates'
        help_text = _(message='Index templates to be queued for rebuilding.')
        label = _(message='Index templates')
        queryset = IndexTemplate.objects.filter(enabled=True)
        permission = permission_index_template_rebuild
        widget_attributes = {'class': 'select2'}


class IndexTemplateNodeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['index'].widget = form_widgets.HiddenInput()
        self.fields['parent'].widget = form_widgets.HiddenInput()
        self.fields['expression'] = ModelTemplateField(
            label=_(message='Template'), model=Document,
            model_variable='document', required=False
        )

    class Meta:
        fields = (
            'parent', 'index', 'expression', 'enabled', 'link_documents'
        )
        model = IndexTemplateNode
