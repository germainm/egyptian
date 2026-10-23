from django.utils.translation import gettext_lazy as _

from mayan.apps.permissions.classes import PermissionNamespace

namespace = PermissionNamespace(
    label=_(message='Cabinets'), name='cabinets'
)

permission_cabinet_add_document = namespace.add_permission(
    label=_(message='Add documents to cabinets'), name='cabinet_add_document'
)
permission_cabinet_create = namespace.add_permission(
    label=_(message='Create cabinets'), name='cabinet_create'
)
permission_cabinet_delete = namespace.add_permission(
    label=_(message='Delete cabinets'), name='cabinet_delete'
)
permission_cabinet_edit = namespace.add_permission(
    label=_(message='Edit cabinets'), name='cabinet_edit'
)
permission_cabinet_remove_document = namespace.add_permission(
    label=_(message='Remove documents from cabinets'), name='cabinet_remove_document'
)
permission_cabinet_view = namespace.add_permission(
    label=_(message='View cabinets'), name='cabinet_view'
)
