from django.utils.translation import gettext, gettext_lazy as _

from mayan.apps.forms import form_fields

from .literals import (
    SOURCE_UNCOMPRESS_API_CHOICE_NEVER, SOURCE_UNCOMPRESS_API_CHOICES,
    SOURCE_UNCOMPRESS_CHOICE_ASK, SOURCE_UNCOMPRESS_INTERACTIVE_CHOICES
)


class SourceBackendMixinCompressed:
    uncompress_choices = SOURCE_UNCOMPRESS_INTERACTIVE_CHOICES
    uncompress_default = SOURCE_UNCOMPRESS_CHOICE_ASK

    @classmethod
    def get_form_field_widgets(cls):
        widgets = super().get_form_field_widgets()

        widgets.update(
            {
                'uncompress': {
                    'class': 'django.forms.widgets.Select', 'kwargs': {
                        'attrs': {'class': 'select2'}
                    }
                }
            }
        )
        return widgets

    @classmethod
    def get_form_fields(cls):
        fields = super().get_form_fields()

        fields.update(
            {
                'uncompress': {
                    'label': _(message='Uncompress'),
                    'class': 'django.forms.ChoiceField',
                    'default': cls.uncompress_default,
                    'help_text': _(
                        message='Whether to expand or not compressed '
                        'archives. Some file types such as PDF, email, and '
                        'Outlook messages can also act as containers for '
                        'other files. When expansion is enabled and one of '
                        'these files holds no attachments, "Always" rejects '
                        'the upload so it is not silently discarded, '
                        '"Always, or keep the file if it expands to nothing" '
                        'stores the file unchanged, and "Always, and also '
                        'keep the original file" always stores the original '
                        'file in addition to any files extracted from it.'
                    ),
                    'kwargs': {
                        'choices': cls.uncompress_choices
                    },
                    'required': True
                }
            }
        )

        return fields

    @classmethod
    def get_form_fieldsets(cls):
        fieldsets = super().get_form_fieldsets()

        fieldsets += (
            (
                _(message='Decompression'), {
                    'fields': ('uncompress',)
                },
            ),
        )

        return fieldsets

    def get_uncompress(self):
        return self.kwargs.get(
            'uncompress', self.uncompress_default
        )

    def get_upload_form_class(self, action):
        backend_instance = self

        super_upload_form_class = super().get_upload_form_class(
            action=action
        )

        class CompressedSourceUploadForm(super_upload_form_class):
            expand_mode = form_fields.ChoiceField(
                choices=SOURCE_UNCOMPRESS_API_CHOICES,
                initial=SOURCE_UNCOMPRESS_API_CHOICE_NEVER,
                label=_(message='Decompression'), required=True,
                help_text=gettext(
                    'Whether and how to expand a compressed or container '
                    'file into individual documents.'
                )
            )

            def __init__(self, *args, **kwargs):
                self.field_order = ['expand_mode']
                super().__init__(*args, **kwargs)

                uncompress = backend_instance.get_uncompress()

                if uncompress != SOURCE_UNCOMPRESS_CHOICE_ASK or action.name == 'document_file_upload':
                    self.fields.pop('expand_mode')

        return CompressedSourceUploadForm
