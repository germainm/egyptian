from mayan.apps.authentication.link_conditions import (
    condition_is_current_user, condition_not_is_current_user
)

from .settings import setting_color_mode_user_selection_enabled


def _color_mode_selection_available():
    return setting_color_mode_user_selection_enabled.value


def condition_color_mode_user_selection_enabled(context, resolved_object):
    if not condition_is_current_user(
        context=context, resolved_object=resolved_object
    ):
        return False

    return _color_mode_selection_available()


def condition_color_mode_user_admin(context, resolved_object):
    if not condition_not_is_current_user(
        context=context, resolved_object=resolved_object
    ):
        return False

    return _color_mode_selection_available()
