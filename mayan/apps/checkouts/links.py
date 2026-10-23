from django.utils.translation import gettext_lazy as _

from mayan.apps.navigation.links import Link

from .icons import (
    icon_check_in_document, icon_check_out_document, icon_check_out_info,
    icon_check_out_list
)
from .permissions import (
    permission_document_check_in, permission_document_check_out,
    permission_document_check_out_detail_view
)


def condition_is_checked_out(context, resolved_object):
    try:
        return context['object'].is_checked_out()
    except KeyError:
        return False


def condition_is_not_checked_out(context, resolved_object):
    try:
        return not context['object'].is_checked_out()
    except KeyError:
        return True


link_check_out_list = Link(
    icon=icon_check_out_list, text=_(message='Checkouts'),
    view='checkouts:check_out_list'
)
link_check_out_document = Link(
    args='object.pk', condition=condition_is_not_checked_out,
    icon=icon_check_out_document,
    permission=permission_document_check_out,
    text=_(message='Check out document'), view='checkouts:check_out_document'
)
link_check_out_document_multiple = Link(
    icon=icon_check_out_document,
    permission=permission_document_check_out, text=_(message='Check out'),
    view='checkouts:check_out_document_multiple'
)
link_check_in_document = Link(
    args='object.pk', icon=icon_check_in_document,
    condition=condition_is_checked_out, text=_(message='Check in document'),
    view='checkouts:check_in_document'
)
link_check_in_document_multiple = Link(
    icon=icon_check_in_document,
    permission=permission_document_check_in, text=_(message='Check in'),
    view='checkouts:check_in_document_multiple'
)
link_check_out_info = Link(
    args='resolved_object.pk', icon=icon_check_out_info,
    permission=permission_document_check_out_detail_view,
    text=_(message='Check in/out'), view='checkouts:check_out_info'
)
