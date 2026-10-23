from django.utils.translation import gettext_lazy as _

from mayan.apps.permissions.classes import PermissionNamespace

namespace = PermissionNamespace(
    label=_(message='Mailing'), name='mailing'
)


permission_mailing_profile_create = namespace.add_permission(
    label=_(message='Create a mailing profile'),
    name='mailing_profile_create'
)
permission_mailing_profile_delete = namespace.add_permission(
    label=_(message='Delete a mailing profile'),
    name='mailing_profile_delete'
)
permission_mailing_profile_edit = namespace.add_permission(
    label=_(message='Edit a mailing profile'), name='mailing_profile_edit'
)
permission_mailing_profile_use = namespace.add_permission(
    label=_(message='Use a mailing profile'), name='mailing_profile_use'
)
permission_mailing_profile_view = namespace.add_permission(
    label=_(message='View a mailing profile'), name='mailing_profile_view'
)


permission_send_document_link = namespace.add_permission(
    label=_(message='Send document link via email'), name='mail_link'
)


permission_send_document_file_attachment = namespace.add_permission(
    label=_(message='Send document file via email'),
    name='mail_document_file_attachment'
)
permission_send_document_file_link = namespace.add_permission(
    label=_(message='Send document file link via email'),
    name='mail_document_file_link'
)


permission_send_document_version_attachment = namespace.add_permission(
    label=_(message='Send document version via email'),
    name='mail_document_version_attachment'
)
permission_send_document_version_link = namespace.add_permission(
    label=_(message='Send document version link via email'),
    name='mail_document_version_link'
)
