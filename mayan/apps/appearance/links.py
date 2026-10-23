from django.utils.translation import gettext_lazy as _

from mayan.apps.navigation.links import Link
from mayan.apps.user_management.permissions import permission_user_edit

from .icons import icon_ajax_refresh, icon_theme

from .link_conditions import (
    condition_theme_user_admin, condition_theme_user_selection_enabled
)

link_ajax_refresh = Link(
    icon=icon_ajax_refresh, html_extra_classes='appearance-link-ajax-refresh',
    title=_(message='Reload content')
)
link_user_current_theme_edit = Link(
    condition=condition_theme_user_selection_enabled,
    icon=icon_theme,
    text=_(message='Themes'), view='appearance:user_current_theme_edit'
)
link_user_theme_edit = Link(
    args='resolved_object.pk', condition=condition_theme_user_admin,
    icon=icon_theme, permission=permission_user_edit, text=_(message='Theme'),
    view='appearance:user_theme_edit'
)
