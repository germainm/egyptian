from django.utils.translation import gettext_lazy as _

from mayan.apps.forms import form_widgets, forms

from ..classes import BaseDocumentFilenameGenerator
from ..models import DocumentType, DocumentTypeFilename


class DocumentTypeFilenameGeneratorForm(forms.ModelForm):
    class Meta:
        fields = (
            'filename_generator_backend',
            'filename_generator_backend_arguments'
        )
        model = DocumentType
        widgets = {
            'filename_generator_backend': form_widgets.Select(
                choices=BaseDocumentFilenameGenerator.get_choices()
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields['filename_generator_backend']
        field.choices = BaseDocumentFilenameGenerator.get_choices()


class DocumentTypeFilenameForm_create(forms.ModelForm):
    class Meta:
        fields = ('filename',)
        model = DocumentTypeFilename


class DocumentTypeFilteredSelectForm(forms.FilteredSelectionForm):
    class Meta:
        field_name = 'document_type'
        label = _(message='Document type')
        queryset = DocumentType.objects.all()
        required = True
        widget_attributes = {'class': 'select2', 'size': 10}
