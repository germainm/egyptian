from django.utils.translation import gettext_lazy as _

from mayan.apps.permissions.classes import PermissionNamespace

namespace = PermissionNamespace(
    label=_(message='Sequences'), name='sequences'
)

permission_sequence_create = namespace.add_permission(
    label=_(message='Create sequences'), name='sequence_create'
)
permission_sequence_delete = namespace.add_permission(
    label=_(message='Delete sequences'), name='sequence_delete'
)
permission_sequence_edit = namespace.add_permission(
    label=_(message='Edit sequences'), name='sequence_edit'
)
permission_sequence_reset = namespace.add_permission(
    label=_(message='Reset sequences'), name='sequence_reset'
)
permission_sequence_use = namespace.add_permission(
    label=_(message='Use sequences'), name='sequence_use'
)
permission_sequence_view = namespace.add_permission(
    label=_(message='View sequences'), name='sequence_view'
)
