from django.template import Library
from django.utils.translation import get_language_bidi

from ..classes import ColorMode

register = Library()


@register.simple_tag(name='appearance_bootstrap_color_mode_get', takes_context=True)
def tag_appearance_bootstrap_color_mode_get(context):
    """
    Resolve the Bootstrap color mode for the current request. Used to set the
    `data-bs-theme` attribute on the root element per user.
    """
    return ColorMode.get_for_request(request=context.get('request'))


@register.simple_tag(name='appearance_bootstrap_text_direction_get')
def tag_appearance_bootstrap_text_direction_get():
    """
    Resolve the text direction of the active language. Returns `rtl` for
    right-to-left (bidirectional) languages and `ltr` otherwise. Used to set
    the `dir` attribute on the root element and to select the matching
    Bootstrap stylesheet variant.
    """
    return 'rtl' if get_language_bidi() else 'ltr'
