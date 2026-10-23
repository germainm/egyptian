from django.utils.translation import gettext_lazy as _

from mayan.apps.forms import form_fields, form_widgets, forms, formsets

from ..fields import DocumentVersionPageField, ThumbnailFormField

from .document_version_page_form_mixins import FormSetExtraFormKwargsMixin


class DocumentVersionPageForm(forms.Form):
    document_version_page = DocumentVersionPageField()

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop('instance', None)
        transformation_instance_list = kwargs.pop(
            'transformation_instance_list', ()
        )
        super().__init__(*args, **kwargs)
        self.fields['document_version_page'].initial = instance
        self.fields['document_version_page'].widget.attrs.update(
            {
                'transformation_instance_list': transformation_instance_list
            }
        )


class DocumentVersionPageMappingForm(forms.Form):
    source_content_type = form_fields.IntegerField(
        label=_(message='Content type'), widget=form_widgets.HiddenInput
    )
    source_object_id = form_fields.IntegerField(
        label=_(message='Object ID'), widget=form_widgets.HiddenInput
    )
    source_label = form_fields.CharField(
        label=_(message='Source'), required=False,
        widget=forms.TextInput(
            attrs={'readonly': 'readonly'}
        )
    )
    source_thumbnail = ThumbnailFormField(required=False)
    target_page_number = form_fields.ChoiceField(
        choices=(), label=_(message='Destination page number'),
        required=False, widget=form_widgets.Select(
            attrs={'size': 1, 'class': 'select2'}
        )
    )

    def __init__(self, *args, **kwargs):
        target_page_number_choices = kwargs.pop(
            'target_page_number_choices', ()
        )
        super().__init__(*args, **kwargs)
        self.fields['target_page_number'].choices = target_page_number_choices


class DocumentVersionPageMappingFormSet(
    FormSetExtraFormKwargsMixin, formsets.formset_factory(
        form=DocumentVersionPageMappingForm, extra=0
    )
):
    def clean(self):
        set_of_target_page_numbers = set()
        for form in self.forms:
            cleaned_data_entry = form.cleaned_data
            target_page_number = cleaned_data_entry['target_page_number']
            if target_page_number != '0':
                if target_page_number in set_of_target_page_numbers:
                    form.add_error(
                        error=_(
                            message='Target page number can\'t be repeated.'
                        ), field='target_page_number'
                    )
                else:
                    set_of_target_page_numbers.add(target_page_number)
