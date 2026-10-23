from django.utils.translation import gettext_lazy as _

from mayan.apps.rest_api import serializers

from .classes import ColorMode


class ColorModeSettingSerializer(serializers.Serializer):
    color_mode = serializers.ChoiceField(
        choices=(), help_text=_(
            message='Name of the color mode (e.g. `light` or `dark`).'
        ), label=_(message='Color mode')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['color_mode'].choices = ColorMode.get_choices()
