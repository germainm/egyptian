from django.utils.translation import gettext_lazy as _

from mayan.apps.permissions.classes import PermissionNamespace

namespace = PermissionNamespace(
    label=_(message='Documents'), name='documents'
)


permission_document_change_type = namespace.add_permission(
    label=_(message='Change type of documents'), name='document_change_type'
)
permission_document_create = namespace.add_permission(
    label=_(message='Create documents'), name='document_create'
)
permission_document_edit = namespace.add_permission(
    label=_(message='Edit documents'), name='document_edit'
)
permission_document_properties_edit = namespace.add_permission(
    label=_(message='Edit document properties'), name='document_properties_edit'
)
permission_document_tools = namespace.add_permission(
    label=_(message='Execute document modifying tools'), name='document_tools'
)
permission_document_view = namespace.add_permission(
    label=_(message='View documents'), name='document_view'
)


permission_document_file_delete = namespace.add_permission(
    label=_(message='Delete document files'), name='document_file_delete'
)
permission_document_file_edit = namespace.add_permission(
    label=_(message='Edit document files'), name='document_file_edit'
)
permission_document_file_new = namespace.add_permission(
    label=_(message='Create new document files'), name='document_file_new'
)
permission_document_file_print = namespace.add_permission(
    label=_(message='Print document files'), name='document_file_print'
)
permission_document_file_tools = namespace.add_permission(
    label=_(message='Execute document file modifying tools'),
    name='document_file_tools'
)
permission_document_file_view = namespace.add_permission(
    label=_(message='View document files'),
    name='document_file_view'
)


permission_document_version_create = namespace.add_permission(
    label=_(message='Create document versions'),
    name='document_version_create'
)
permission_document_version_delete = namespace.add_permission(
    label=_(message='Delete document versions'),
    name='document_version_delete'
)
permission_document_version_edit = namespace.add_permission(
    label=_(message='Edit document versions'),
    name='document_version_edit'
)
permission_document_version_print = namespace.add_permission(
    label=_(message='Print document versions'), name='document_version_print'
)
permission_document_version_view = namespace.add_permission(
    label=_(message='View document versions'),
    name='document_version_view'
)


document_type_namespace = PermissionNamespace(
    label=_(message='Document types'), name='documents_types'
)
permission_document_type_create = document_type_namespace.add_permission(
    label=_(message='Create document types'), name='document_type_create'
)
permission_document_type_delete = document_type_namespace.add_permission(
    label=_(message='Delete document types'), name='document_type_delete'
)
permission_document_type_edit = document_type_namespace.add_permission(
    label=_(message='Edit document types'), name='document_type_edit'
)
permission_document_type_view = document_type_namespace.add_permission(
    label=_(message='View document types'), name='document_type_view'
)


permission_trashed_document_restore = namespace.add_permission(
    label=_(message='Restore trashed document'), name='document_restore'
)
permission_trashed_document_delete = namespace.add_permission(
    label=_(message='Delete trashed documents'), name='document_delete'
)
permission_document_trash = namespace.add_permission(
    label=_(message='Trash documents'), name='document_trash'
)
permission_trash_empty = namespace.add_permission(
    label=_(message='Empty trash'), name='document_empty_trash'
)
