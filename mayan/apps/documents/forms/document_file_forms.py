from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _

from mayan.apps.forms import form_widgets, forms

from ..fields import DocumentFileField
from ..models.document_file_models import DocumentFile


class DocumentFileForm(forms.ModelForm):
    class Meta:
        fields = ('filename', 'comment',)
        model = DocumentFile


class DocumentFilePreviewForm(forms.Form):
    def __init__(self, *args, **kwargs):
        document_file = kwargs.pop('instance', None)
        transformation_instance_list = kwargs.pop(
            'transformation_instance_list', ()
        )
        super().__init__(*args, **kwargs)
        self.fields['document_file'].initial = document_file
        self.fields['document_file'].widget.attrs.update(
            {'transformation_instance_list': transformation_instance_list}
        )

    document_file = DocumentFileField()


class DocumentFilePropertiesForm(forms.DetailForm):
    fieldsets = (
        (
            _(message='Original'), {
                'fields': ('filename', 'size')
            }
        ), (
            _(message='Detected'), {
                'fields': ('mimetype', 'encoding', 'pages')
            }
        ), (
            _(message='Storage'), {
                'fields': ('file', 'exists', 'checksum')
            }
        ), (
            _(message='Other'), {
                'fields': ('timestamp', 'comment')
            }
        )
    )

    class Meta:
        extra_fields = [
            {
                'label': _(message='Date added'),
                'field': 'timestamp',
                'widget': form_widgets.DateTimeInput
            },
            {
                'label': _(message='MIME type'),
                'field': 'mimetype'
            },
            {
                'label': _(message='Encoding'),
                'field': 'encoding'
            },
            {
                'label': _(message='Size'),
                'func': lambda document_file: filesizeformat(
                    bytes_=document_file.size
                ) if document_file.size else '-', 'field': 'size'
            },
            {
                'label': _(message='Exists in storage'), 'field': 'exists'
            },
            {
                'label': _(message='Path in storage'), 'field': 'file'
            },
            {
                'label': _(message='Checksum'), 'field': 'checksum'
            },
            {
                'label': _(message='Pages'),
                'func': lambda document_file: document_file.pages.count(),
                'field': 'pages'
            }
        ]
        fields = ('filename', 'comment',)
        model = DocumentFile
