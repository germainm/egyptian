import yaml

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.serialization import yaml_load
from mayan.apps.forms import form_fields, form_widgets, forms
from mayan.apps.templating.fields import TemplateField


class SettingForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setting = self.initial['setting']

        choices = self.setting.get_value_choices()

        help_text = self.setting.help_text or _(
            message='Enter the new setting value.'
        )

        if choices:
            self.fields['value'] = form_fields.ChoiceField(
                choices=list(
                    zip(choices, choices)
                ), help_text=help_text, label=_(message='Value'),
                required=True, widget=form_widgets.Select(
                    attrs={'class': 'select2'}
                )
            )
        else:
            self.fields['value'] = TemplateField(
                initial_help_text=help_text, label=_(message='Value'),
                required=False
            )

        self.fields['value'].initial = self.setting.get_display_value()

    def clean(self):
        try:
            yaml_load(
                stream=self.cleaned_data['value']
            )
        except yaml.YAMLError:
            raise ValidationError(
                message=_(
                    message='"%s" not a valid entry.'
                ) % self.cleaned_data['value']
            )
        else:
            self.setting.do_value_raw_validate(
                raw_value=self.cleaned_data['value']
            )
