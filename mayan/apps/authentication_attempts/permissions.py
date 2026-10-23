from django.utils.translation import gettext_lazy as _

from mayan.apps.permissions.classes import PermissionNamespace

namespace = PermissionNamespace(
    label=_(message='Authentication attempts'),
    name='authentication_attempts'
)

permission_login_attempt_view = namespace.add_permission(
    label=_(message='View the login attempts of all users'),
    name='login_attempt_view'
)
