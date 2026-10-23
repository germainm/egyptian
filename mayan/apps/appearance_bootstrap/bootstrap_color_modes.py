from django.utils.translation import gettext_lazy as _

from .classes import ColorMode

color_mode_light = ColorMode(
    default=True, label=_(message='Light'), name='light',
    theme_color='#ffffff'
)
color_mode_dark = ColorMode(
    label=_(message='Dark'), name='dark', theme_color='#212529'
)
