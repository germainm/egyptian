from django.utils.translation import gettext_lazy as _

from mayan.apps.forms import form_fields, form_widgets, forms

from .classes import ColorMode


class ColorModeForm(forms.Form):
    color_mode = form_fields.ChoiceField(
        help_text=_(message='Color mode used for the interface.'),
        label=_(message='Color mode'), widget=form_widgets.RadioSelect
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['color_mode'].choices = ColorMode.get_choices()
