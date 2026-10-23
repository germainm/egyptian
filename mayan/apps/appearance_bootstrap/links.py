from django.utils.translation import gettext_lazy as _

from mayan.apps.navigation.links import Link
from mayan.apps.user_management.permissions import permission_user_edit

from .icons import icon_color_mode

from .link_conditions import (
    condition_color_mode_user_admin,
    condition_color_mode_user_selection_enabled
)

link_user_current_color_mode = Link(
    condition=condition_color_mode_user_selection_enabled,
    icon=icon_color_mode, text=_(message='Color modes'),
    view='appearance_bootstrap:user_current_color_mode_edit'
)
link_user_color_mode_edit = Link(
    args='resolved_object.pk', condition=condition_color_mode_user_admin,
    icon=icon_color_mode, permission=permission_user_edit,
    text=_(message='Color mode'),
    view='appearance_bootstrap:user_color_mode_edit'
)
