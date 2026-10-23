from django.utils.translation import gettext_lazy as _

from mayan.apps.permissions.classes import PermissionNamespace

namespace = PermissionNamespace(
    label=_(message='Authentication'), name='authentication'
)

permission_account_lockout_reset = namespace.add_permission(
    label=_(message='Reset account lockout for users'),
    name='account_lockout_reset'
)
permission_users_impersonate = namespace.add_permission(
    label=_(message='Impersonate users'), name='users_impersonate'
)
