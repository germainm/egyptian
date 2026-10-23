from django.utils.translation import gettext_lazy as _

from mayan.apps.rest_api import serializers

from .classes import Theme


class ThemeSettingSerializer(serializers.Serializer):
    theme = serializers.ChoiceField(
        choices=(), help_text=_(
            message='Name of the theme (frontend stylesheet).'
        ), label=_(message='Theme')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['theme'].choices = Theme.get_choices()
