from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from mayan.apps.forms import form_fields, form_widgets, forms, formsets
from mayan.apps.forms.literals import EMPTY_LABEL
from mayan.apps.templating.fields import TemplateField

from .classes import MetadataParser, MetadataValidator
from .models.metadata_type_models import MetadataType


class DocumentMetadataForm(forms.Form):
    metadata_type_id = form_fields.CharField(
        label=_(message='ID'), widget=form_widgets.HiddenInput
    )
    metadata_type_name = form_fields.CharField(
        label=_(message='Name'), required=False,
        widget=form_widgets.TextInput(
            attrs={
                'readonly': 'readonly'
            }
        )
    )
    value = form_fields.CharField(
        label=_(message='Value'), required=False, widget=form_widgets.TextInput(
            attrs={'class': 'metadata-value'}
        )
    )
    update = form_fields.BooleanField(
        initial=True, label=_(message='Update'), required=False
    )

    class Media:
        js = ('metadata/js/metadata_form.js',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'initial' in kwargs:
            self.metadata_type = kwargs['initial']['metadata_type']
            self.document_type = kwargs['initial']['document_type']
            required_string = ''

            required = self.metadata_type.get_required_for(
                document_type=self.document_type
            )

            if required:
                required_string = ' (%s)' % _(message='Required')
            else:
                self.fields['update'].initial = False

            field_metadata_type_label = self.metadata_type.label or self.metadata_type.name

            self.fields['metadata_type_name'].initial = '{}{}'.format(
                field_metadata_type_label, required_string
            )

            self.fields['metadata_type_id'].initial = self.metadata_type.pk

            if self.metadata_type.lookup:
                try:
                    self.fields['value'] = form_fields.ChoiceField(
                        label=self.fields['value'].label
                    )
                    choices = self.metadata_type.get_lookup_values()
                    choices = list(
                        zip(choices, choices)
                    )
                    if not required:
                        choices.insert(
                            0, ('', EMPTY_LABEL)
                        )
                    self.fields['value'].choices = choices
                    self.fields['value'].required = required
                    self.fields['value'].widget.attrs.update(
                        {'class': 'metadata-value'}
                    )
                except Exception as exception:
                    self.fields['value'].initial = _(
                        message='Lookup value error: %s'
                    ) % exception
                    self.fields['value'].widget = form_widgets.TextInput(
                        attrs={'readonly': 'readonly'}
                    )

            if self.metadata_type.default:
                try:
                    self.fields[
                        'value'
                    ].initial = self.metadata_type.get_default_value()
                except Exception as exception:
                    self.fields['value'].initial = _(
                        message='Default value error: %s'
                    ) % exception
                    self.fields['value'].widget = form_widgets.TextInput(
                        attrs={'readonly': 'readonly'}
                    )

    def clean(self):
        metadata_type = getattr(self, 'metadata_type', None)

        if metadata_type:
            required = metadata_type.get_required_for(
                document_type=self.document_type
            )

            if required and not self.initial.get('value_existing'):
                if not self.cleaned_data.get('update') or not self.cleaned_data.get('value'):
                    raise ValidationError(
                        message={
                            'value': _(
                                message='"%s" is required for this document '
                                'type.'
                            ) % metadata_type.label
                        }
                    )

            if self.cleaned_data.get('update'):
                self.cleaned_data['value'] = metadata_type.validate_value(
                    document_type=self.document_type,
                    value=self.cleaned_data.get('value')
                )

        return self.cleaned_data


DocumentMetadataFormSet = formsets.formset_factory(
    form=DocumentMetadataForm, extra=0
)


class DocumentMetadataAddForm(forms.Form):
    metadata_type = form_fields.ModelMultipleChoiceField(
        help_text=_(message='Metadata types to be added to the selected documents.'),
        label=_(message='Metadata type'), queryset=MetadataType.objects.all(),
        widget=form_widgets.SelectMultiple(
            attrs={'class': 'select2'}
        )
    )

    def __init__(self, *args, **kwargs):
        document_type = kwargs.pop('document_type', None)

        if document_type:
            queryset = kwargs.pop(
                'queryset', MetadataType.objects.get_for_document_type(
                    document_type=document_type
                )
            )
        else:
            queryset = MetadataType.objects.none()

        super().__init__(*args, **kwargs)

        self.fields['metadata_type'].queryset = queryset


class DocumentMetadataRemoveForm(DocumentMetadataForm):
    update = form_fields.BooleanField(
        initial=False, label=_(message='Remove'), required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('value')

    def clean(self):
        return super(forms.Form, self).clean()


DocumentMetadataRemoveFormSet = formsets.formset_factory(
    form=DocumentMetadataRemoveForm, extra=0
)


class MetadataTypeForm(forms.ModelForm):
    fieldsets = (
        (
            _(message='Basic'), {
                'fields': ('name', 'label')
            }
        ), (
            _(message='Values'), {
                'fields': ('default', 'lookup')
            }
        ), (
            _(message='Validation'), {
                'fields': ('validation', 'validation_arguments')
            }
        ), (
            _(message='Parsing'), {
                'fields': ('parser', 'parser_arguments')
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['default'] = TemplateField(
            initial_help_text=self.fields['default'].help_text,
            required=False
        )
        self.fields['lookup'] = TemplateField(
            context_entry_name_list=('groups', 'users'),
            initial_help_text=self.fields['lookup'].help_text,
            required=False
        )
        self.fields['parser'].widget = form_widgets.Select(
            choices=MetadataParser.get_choices(add_blank=True)
        )
        self.fields['validation'].widget = form_widgets.Select(
            choices=MetadataValidator.get_choices(add_blank=True)
        )

    class Meta:
        fields = (
            'name', 'label', 'default', 'lookup', 'validation',
            'validation_arguments', 'parser', 'parser_arguments'
        )
        model = MetadataType


class DocumentTypeMetadataTypeRelationshipForm(forms.RelationshipForm):
    RELATIONSHIP_TYPE_NONE = 'none'
    RELATIONSHIP_TYPE_OPTIONAL = 'optional'
    RELATIONSHIP_TYPE_REQUIRED = 'required'
    RELATIONSHIP_CHOICES = (
        (RELATIONSHIP_TYPE_NONE, _(message='None')),
        (RELATIONSHIP_TYPE_OPTIONAL, _(message='Optional')),
        (RELATIONSHIP_TYPE_REQUIRED, _(message='Required')),
    )

    def get_relationship_type(self):
        queryset_relationship = self.get_queryset_relationship()

        if queryset_relationship.exists():
            if queryset_relationship.get().required:
                return self.RELATIONSHIP_TYPE_REQUIRED
            else:
                return self.RELATIONSHIP_TYPE_OPTIONAL
        else:
            return self.RELATIONSHIP_TYPE_NONE

    def save_relationship_none(self):
        instance = self.get_relationship_instance()
        instance._event_actor = self._event_actor
        instance.delete()

    def save_relationship_optional(self):
        instance = self.get_relationship_instance()
        instance.required = False
        instance._event_actor = self._event_actor
        instance.save()

    def save_relationship_required(self):
        instance = self.get_relationship_instance()
        instance.required = True
        instance._event_actor = self._event_actor
        instance.save()


DocumentTypeMetadataTypeRelationshipFormSetBase = formsets.formset_factory(
    form=DocumentTypeMetadataTypeRelationshipForm, extra=0
)


class DocumentTypeMetadataTypeRelationshipFormSet(
    DocumentTypeMetadataTypeRelationshipFormSetBase
):
    def __init__(self, *args, **kwargs):
        _event_actor = kwargs.pop('_event_actor')
        super().__init__(*args, **kwargs)
        self.form_kwargs.update(
            {'_event_actor': _event_actor}
        )
