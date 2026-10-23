import markdown
import nh3

from django.utils.safestring import mark_safe

from mayan.apps.forms import form_widgets, forms

from .literals import MARKDOWN_ATTRIBUTES_ALLOWED, MARKDOWN_EXTENSION_LIST


class LicenseForm(forms.FileDisplayForm):
    DIRECTORY = ()
    FILENAME = 'LICENSE'


class FileDisplayMarkdownForm(forms.FileDisplayForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        source = self.fields['text'].initial

        self.fields['text'].initial = self.get_rendered(source=source)
        self.fields['text'].widget = form_widgets.PlainWidget()

    def get_rendered(self, source):
        instance_markdown = markdown.Markdown(
            extensions=MARKDOWN_EXTENSION_LIST
        )

        html = instance_markdown.convert(source=source)

        html_clean = nh3.clean(
            attributes=MARKDOWN_ATTRIBUTES_ALLOWED, html=html
        )

        return mark_safe(s=html_clean)


class TrademarkPolicyForm(FileDisplayMarkdownForm):
    DIRECTORY = ()
    FILENAME = 'TRADEMARK_POLICY.md'
