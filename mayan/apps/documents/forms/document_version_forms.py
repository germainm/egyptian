from django.utils.translation import gettext_lazy as _

from mayan.apps.forms import form_fields, forms

from ..classes import DocumentVersionModification
from ..fields import DocumentVersionField
from ..models.document_version_models import DocumentVersion


class DocumentVersionForm(forms.ModelForm):
    class Meta:
        fields = ('comment',)
        model = DocumentVersion


class DocumentVersionModificationBackendForm(forms.Form):
    backend = form_fields.ChoiceField(
        choices=(), help_text=_(
            message='The backend that will be executed against the selected '
            'document version.'
        ), label=_(message='Backend')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['backend'].choices = DocumentVersionModification.get_choices()


class DocumentVersionPreviewForm(forms.Form):
    document_version = DocumentVersionField()

    def __init__(self, *args, **kwargs):
        document_version = kwargs.pop('instance', None)
        transformation_instance_list = kwargs.pop(
            'transformation_instance_list', ()
        )
        super().__init__(*args, **kwargs)
        self.fields['document_version'].initial = document_version
        self.fields['document_version'].widget.attrs.update(
            {
                'transformation_instance_list': transformation_instance_list
            }
        )
