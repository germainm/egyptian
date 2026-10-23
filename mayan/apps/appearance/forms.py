from django.utils.translation import gettext_lazy as _

from mayan.apps.forms import form_fields, form_widgets, forms

from .classes import Theme


class ThemeForm(forms.Form):
    theme = form_fields.ChoiceField(
        help_text=_(message='Theme (stylesheet) used for the interface.'),
        label=_(message='Theme'), widget=form_widgets.RadioSelect
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['theme'].choices = Theme.get_choices()
