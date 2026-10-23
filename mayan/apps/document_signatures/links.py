from django.apps import apps
from django.utils.translation import gettext_lazy as _

from mayan.apps.navigation.links import Link

from .icons import (
    icon_document_file_all_signature_refresh,
    icon_document_file_all_signature_verify,
    icon_document_file_signature_detached_delete,
    icon_document_file_signature_detached_create,
    icon_document_file_signature_detail,
    icon_document_file_signature_detached_download,
    icon_document_file_signature_detached_upload,
    icon_document_file_signature_embedded_create,
    icon_document_file_signature_list
)
from .permissions import (
    permission_document_file_sign_detached,
    permission_document_file_sign_embedded,
    permission_document_file_signature_delete,
    permission_document_file_signature_download,
    permission_document_file_signature_upload,
    permission_document_file_signature_verify,
    permission_document_file_signature_view
)


def condition_is_detached_signature(context, resolved_object):
    SignatureBaseModel = apps.get_model(
        app_label='document_signatures', model_name='SignatureBaseModel'
    )

    return SignatureBaseModel.objects.select_subclasses().get(
        pk=context['resolved_object'].pk
    ).is_detached



link_document_file_signature_detached_create = Link(
    args='resolved_object.pk',
    icon=icon_document_file_signature_detached_create,
    permission=permission_document_file_sign_detached,
    text=_(message='Sign detached'),
    view='signatures:document_file_signature_detached_create'
)
link_document_file_signature_detached_delete = Link(
    args='resolved_object.pk', condition=condition_is_detached_signature,
    icon=icon_document_file_signature_detached_delete,
    permission=permission_document_file_signature_delete,
    tags='dangerous', text=_(message='Delete'),
    view='signatures:document_file_signature_detached_delete'
)
link_document_file_signature_detached_download = Link(
    args='resolved_object.pk',
    icon=icon_document_file_signature_detached_download,
    condition=condition_is_detached_signature,
    permission=permission_document_file_signature_download,
    text=_(message='Download'),
    view='signatures:document_file_signature_detached_download'
)
link_document_file_signature_detached_upload = Link(
    args='resolved_object.pk',
    icon=icon_document_file_signature_detached_upload,
    permission=permission_document_file_signature_upload,
    text=_(message='Upload signature'),
    view='signatures:document_file_signature_detached_upload'
)


link_document_file_signature_embedded_create = Link(
    args='resolved_object.pk',
    icon=icon_document_file_signature_embedded_create,
    permission=permission_document_file_sign_embedded,
    text=_(message='Sign embedded'),
    view='signatures:document_file_signature_embedded_create'
)


link_document_file_signature_detail = Link(
    args='resolved_object.pk',
    icon=icon_document_file_signature_detail,
    permission=permission_document_file_signature_view,
    text=_(message='Details'), view='signatures:document_file_signature_detail'
)

link_document_file_signature_list = Link(
    args='resolved_object.pk', icon=icon_document_file_signature_list,
    permission=permission_document_file_signature_view,
    text=_(message='Signatures'), view='signatures:document_file_signature_list'
)


link_document_file_all_signature_refresh = Link(
    icon=icon_document_file_all_signature_refresh,
    permission=permission_document_file_signature_verify,
    text=_(message='Refresh all signatures'),
    view='signatures:all_document_file_signature_refresh'
)
link_document_file_all_signature_verify = Link(
    icon=icon_document_file_all_signature_verify,
    permission=permission_document_file_signature_verify,
    text=_(message='Verify all documents'),
    view='signatures:all_document_file_signature_verify'
)
