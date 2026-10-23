from django.utils.translation import gettext_lazy as _

from mayan.apps.permissions.classes import PermissionNamespace

namespace = PermissionNamespace(
    label=_(message='Sources setup'), name='sources_setup'
)


permission_document_file_sources_metadata_view = namespace.add_permission(
    label=_(message='View document file source metadata'),
    name='source_metadata_view'
)


permission_sources_create = namespace.add_permission(
    label=_(message='Create new document sources'),
    name='sources_setup_create'
)
permission_sources_delete = namespace.add_permission(
    label=_(message='Delete document sources'), name='sources_setup_delete'
)
permission_sources_edit = namespace.add_permission(
    label=_(message='Edit document sources'), name='sources_setup_edit'
)
permission_sources_view = namespace.add_permission(
    label=_(message='View existing document sources'),
    name='sources_setup_view'
)
