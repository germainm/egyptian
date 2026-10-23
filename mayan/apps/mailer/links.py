from django.utils.translation import gettext_lazy as _

from mayan.apps.navigation.links import Link
from mayan.apps.navigation.utils import factory_condition_queryset_access

from .icons import (
    icon_document_file_attachment_send_multiple,
    icon_document_file_attachment_send_single,
    icon_document_file_link_send_multiple,
    icon_document_file_link_send_single, icon_document_link_send_multiple,
    icon_document_link_send_single,
    icon_document_version_attachment_send_single,
    icon_document_version_attachment_send_multiple,
    icon_document_version_link_send_multiple,
    icon_document_version_link_send_single, icon_mailing_profile_create,
    icon_mailing_profile_delete, icon_mailing_profile_edit,
    icon_mailing_profile_list, icon_mailing_profile_test
)
from .permissions import (
    permission_mailing_profile_create, permission_mailing_profile_delete,
    permission_mailing_profile_edit, permission_mailing_profile_use,
    permission_mailing_profile_view, permission_send_document_file_attachment,
    permission_send_document_file_link, permission_send_document_link,
    permission_send_document_version_attachment,
    permission_send_document_version_link
)


link_document_link_send_multiple = Link(
    icon=icon_document_link_send_multiple,
    text=_(message='Email document link'),
    view='mailer:send_document_link_multiple'
)
link_document_link_send_single = Link(
    args='resolved_object.pk', icon=icon_document_link_send_single,
    permission=permission_send_document_link,
    text=_(message='Email document link'),
    view='mailer:send_document_link_single'
)


link_document_file_attachment_send_multiple = Link(
    icon=icon_document_file_attachment_send_multiple,
    text=_(message='Email document file'),
    view='mailer:send_document_file_attachment_multiple'
)
link_document_file_attachment_send_single = Link(
    args='resolved_object.pk',
    icon=icon_document_file_attachment_send_single,
    permission=permission_send_document_file_attachment,
    text=_(message='Email document file'),
    view='mailer:send_document_file_attachment_single'
)
link_document_file_link_send_multiple = Link(
    icon=icon_document_file_link_send_multiple,
    text=_(message='Email document file link'),
    view='mailer:send_document_file_link_multiple'
)
link_document_file_link_send_single = Link(
    args='resolved_object.pk', icon=icon_document_file_link_send_single,
    permission=permission_send_document_file_link,
    text=_(message='Email document file link'),
    view='mailer:send_document_file_link_single'
)


link_document_version_attachment_send_single = Link(
    args='resolved_object.pk',
    icon=icon_document_version_attachment_send_single,
    permission=permission_send_document_version_attachment,
    text=_(message='Email document version'),
    view='mailer:send_document_version_attachment_single'
)
link_document_version_attachment_send_multiple = Link(
    icon=icon_document_version_attachment_send_multiple,
    text=_(message='Email document version'),
    view='mailer:send_document_version_attachment_multiple'
)
link_document_version_link_send_single = Link(
    args='resolved_object.pk', icon=icon_document_version_link_send_single,
    permission=permission_send_document_version_link,
    text=_(message='Email document version link'),
    view='mailer:send_document_version_link_single'
)
link_document_version_link_send_multiple = Link(
    icon=icon_document_version_link_send_multiple,
    text=_(message='Email link version'),
    view='mailer:send_document_version_link_multiple'
)


link_mailing_profile_create = Link(
    icon=icon_mailing_profile_create,
    permission=permission_mailing_profile_create,
    text=_(message='Create mailing profile'),
    view='mailer:mailing_profile_backend_selection'
)
link_mailing_profile_delete = Link(
    args='resolved_object.pk', icon=icon_mailing_profile_delete,
    permission=permission_mailing_profile_delete, tags='dangerous',
    text=_(message='Delete'), view='mailer:mailing_profile_delete'
)
link_mailing_profile_edit = Link(
    args='object.pk', icon=icon_mailing_profile_edit,
    permission=permission_mailing_profile_edit, text=_(message='Edit'),
    view='mailer:mailing_profile_edit'
)
link_mailing_profile_list = Link(
    icon=icon_mailing_profile_list, text=_(message='Mailing profiles'),
    view='mailer:mailing_profile_list'
)
link_mailing_profile_setup = Link(
    condition=factory_condition_queryset_access(
        app_label='mailer', model_name='UserMailer',
        object_permission=permission_mailing_profile_view,
        view_permission=permission_mailing_profile_create,
    ), icon=icon_mailing_profile_list, text=_(message='Mailing profiles'),
    view='mailer:mailing_profile_list'
)
link_mailing_profile_test = Link(
    args='object.pk', icon=icon_mailing_profile_test,
    permission=permission_mailing_profile_use, text=_(message='Test'),
    view='mailer:mailing_profile_test'
)
