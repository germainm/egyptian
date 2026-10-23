from mayan.apps.authentication.link_conditions import (
    condition_is_current_user, condition_not_is_current_user
)

from .classes import Theme
from .settings import setting_theme_user_selection_enabled


def _theme_selection_available():
    return setting_theme_user_selection_enabled.value and len(
        Theme.get_all()
    ) > 1


def condition_theme_user_selection_enabled(context, resolved_object):
    if not condition_is_current_user(
        context=context, resolved_object=resolved_object
    ):
        return False

    return _theme_selection_available()


def condition_theme_user_admin(context, resolved_object):
    if not condition_not_is_current_user(
        context=context, resolved_object=resolved_object
    ):
        return False

    return _theme_selection_available()
