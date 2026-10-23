from django.utils.translation import gettext_lazy as _

from mayan.apps.authentication.link_conditions import (
    condition_is_current_user, condition_not_is_current_user
)
from mayan.apps.navigation.links import Link

from .icons import (
    icon_login_attempt_list, icon_user_current_login_attempt_list,
    icon_user_login_attempt_list
)
from .permissions import permission_login_attempt_view

link_login_attempt_list = Link(
    icon=icon_login_attempt_list,
    permission=permission_login_attempt_view,
    text=_(message='Login attempts'),
    view='authentication_attempts:login_attempt_list'
)
link_user_current_login_attempt_list = Link(
    condition=condition_is_current_user,
    icon=icon_user_current_login_attempt_list,
    text=_(message='Login attempts'),
    view='authentication_attempts:user_current_login_attempt_list'
)
link_user_login_attempt_list = Link(
    condition=condition_not_is_current_user,
    icon=icon_user_login_attempt_list,
    kwargs={'user_id': 'resolved_object.pk'},
    permission=permission_login_attempt_view,
    text=_(message='Login attempts'),
    view='authentication_attempts:user_login_attempt_list'
)
