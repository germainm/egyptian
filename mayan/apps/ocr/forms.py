from django.template.loader import render_to_string
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from mayan.apps.forms import form_fields, form_widgets, forms

from .models import DocumentVersionPageOCRContent


class DocumentVersionPageOCRContentDetailForm(forms.Form):
    contents = form_fields.CharField(
        label=_(message='Contents'),
        widget=form_widgets.TextAreaDiv(
            attrs={}
        )
    )

    def __init__(self, *args, **kwargs):
        page = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        content = ''
        self.fields['contents'].initial = ''

        try:
            page_content = page.ocr_content.content
        except DocumentVersionPageOCRContent.DoesNotExist:
            """
            Not critical, just ignore and display empty content.
            """
        else:
            content = conditional_escape(
                str(page_content)
            )

        self.fields['contents'].initial = mark_safe(s=content)


class DocumentVersionPageOCRContentEditForm(forms.ModelForm):
    content = form_fields.CharField(
        label=_(message='Contents'),
        widget=form_widgets.Textarea(
            attrs={'class': 'scrollable'}
        )
    )

    class Meta:
        fields = ('content',)
        model = DocumentVersionPageOCRContent


class DocumentVersionOCRContentForm(forms.Form):
    contents = form_fields.CharField(
        label=_(message='Contents'),
        widget=form_widgets.TextAreaDiv(
            attrs={}
        )
    )

    def __init__(self, *args, **kwargs):
        self.document = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        content = []
        self.fields['contents'].initial = ''
        try:
            document_pages = self.document.pages.all()
        except AttributeError:
            document_pages = []

        for page in document_pages:
            try:
                page_content = page.ocr_content.content
            except DocumentVersionPageOCRContent.DoesNotExist:
                """
                Not critical, just ignore and proceed to next page.
                """
            else:
                text_escaped = conditional_escape(
                    text=str(page_content)
                )
                content.append(text_escaped)

                context = {'page_number': page.page_number}
                content.append(
                    render_to_string(
                        context=context,
                        template_name='ocr/forms/widgets/page_content_divider.html'
                    )
                )

        self.fields['contents'].initial = mark_safe(
            s=''.join(content)
        )
