from django.utils.translation import gettext_lazy as _

from mayan.apps.navigation.links import Link
from mayan.apps.user_management.link_conditions import (
    condition_user_is_not_super_user
)
from mayan.apps.user_management.permissions import permission_user_edit

from .icons import (
    icon_account_lockout_reset, icon_impersonate_start, icon_logout,
    icon_password_change
)
from .link_conditions import (
    condition_account_lockout_enabled,
    condition_account_lockout_reset_single,
    condition_user_has_usable_password_and_can_change_password,
    condition_user_has_usable_password_and_can_change_password_and_is_not_admin
)
from .permissions import (
    permission_account_lockout_reset, permission_users_impersonate
)


link_logout = Link(
    html_extra_classes='non-ajax', icon=icon_logout, method='post',
    text=_(message='Logout'), view='authentication:logout_view'
)
link_password_change = Link(
    condition=condition_user_has_usable_password_and_can_change_password,
    icon=icon_password_change, text=_(message='Change password'),
    view='authentication:password_change_view'
)
link_user_account_lockout_reset_multiple = Link(
    condition=condition_account_lockout_enabled,
    icon=icon_account_lockout_reset,
    permission=permission_account_lockout_reset,
    text=_(message='Reset account lockout'),
    view='authentication:lockout_reset_multiple'
)
link_user_account_lockout_reset_single = Link(
    args='object.id', condition=condition_account_lockout_reset_single,
    icon=icon_account_lockout_reset,
    permission=permission_account_lockout_reset,
    text=_(message='Reset account lockout'),
    view='authentication:lockout_reset_single'
)
link_user_impersonate_form_start = Link(
    icon=icon_impersonate_start,
    permission=permission_users_impersonate, text=_(message='Impersonate user'),
    view='authentication:user_impersonate_form_start'
)
link_user_impersonate_start = Link(
    args='object.id', condition=condition_user_is_not_super_user, icon=icon_impersonate_start,
    permission=permission_users_impersonate, text=_(message='Impersonate'),
    view='authentication:user_impersonate_start'
)
link_user_multiple_set_password = Link(
    icon=icon_password_change, permission=permission_user_edit,
    text=_(message='Set password'), view='authentication:user_multiple_set_password'
)
link_user_set_password = Link(
    args='object.id', condition=condition_user_has_usable_password_and_can_change_password_and_is_not_admin,
    icon=icon_password_change, permission=permission_user_edit,
    text=_(message='Set password'), view='authentication:user_set_password'
)
