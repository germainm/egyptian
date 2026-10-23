import logging
import os

from django.utils.translation import gettext_lazy as _

from mayan.apps.forms import form_fields, form_widgets, forms

from ..models.document_models import Document
from ..settings import setting_language
from ..utils import get_language, get_language_choices

logger = logging.getLogger(name=__name__)


class DocumentForm(forms.ModelForm):
    class Meta:
        fields = ('label', 'description', 'language')
        model = Document

    def __init__(self, *args, **kwargs):
        document_type = kwargs.pop('document_type', None)

        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            document_type = self.instance.document_type
        else:
            self.initial.update(
                {'language': setting_language.value}
            )

        queryset_filenames = document_type.filenames.filter(enabled=True)

        if queryset_filenames:
            self.fields[
                'document_type_available_filenames'
            ] = form_fields.ModelChoiceField(
                queryset=queryset_filenames,
                required=False,
                label=_(message='Quick document rename'),
                widget=forms.Select(
                    attrs={
                        'class': 'select2'
                    }
                )
            )
            self.fields['preserve_extension'] = form_fields.BooleanField(
                label=_(message='Preserve extension'), required=False,
                help_text=_(
                    message='Takes the file extension and moves it to the '
                    'end of the filename allowing operating systems that '
                    'rely on file extensions to open document correctly.'
                )
            )

        self.fields['language'].widget = forms.Select(
            choices=get_language_choices(), attrs={'class': 'select2'}
        )

    def clean(self):
        self.cleaned_data['label'] = self.get_final_label(
            filename=self.cleaned_data.get('label') or self.instance.label
        )

        return self.cleaned_data

    def get_final_label(self, filename):
        if 'document_type_available_filenames' in self.cleaned_data:
            if self.cleaned_data['document_type_available_filenames']:
                if self.cleaned_data['preserve_extension']:
                    filename, extension = os.path.splitext(filename)

                    filename = '{}{}'.format(
                        self.cleaned_data[
                            'document_type_available_filenames'
                        ].filename, extension
                    )
                else:
                    filename = self.cleaned_data[
                        'document_type_available_filenames'
                    ].filename

        return filename


class DocumentPropertiesForm(forms.DetailForm):
    def __init__(self, *args, **kwargs):
        document = kwargs['instance']

        extra_fields = [
            {
                'label': _(message='Date created'),
                'field': 'datetime_created',
                'widget': form_widgets.DateTimeInput
            },
            {
                'label': _(message='UUID'), 'field': 'uuid'
            },
            {
                'label': _(message='Language'),
                'func': lambda x: get_language(
                    language_code=document.language
                )
            }
        ]

        kwargs['extra_fields'] = extra_fields
        super().__init__(*args, **kwargs)

    class Meta:
        fields = ('document_type', 'description')
        model = Document
