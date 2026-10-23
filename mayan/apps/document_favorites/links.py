from django.utils.translation import gettext_lazy as _

from mayan.apps.authentication.link_conditions import (
    condition_user_is_authenticated
)
from mayan.apps.authentication.utils import get_context_user
from mayan.apps.documents.permissions import permission_document_view
from mayan.apps.navigation.links import Link

from .icons import (
    icon_document_favorite_add_multiple, icon_document_favorite_add_single,
    icon_document_favorite_list, icon_document_favorite_remove_multiple,
    icon_document_favorite_remove_single
)


def condition_is_in_favorites(context, resolved_object):
    if condition_user_is_authenticated(
        context=context, resolved_object=resolved_object
    ):
        user = get_context_user(context=context)
        return resolved_object.favorites.filter(user=user).exists()


def condition_not_is_in_favorites(context, resolved_object):
    if condition_user_is_authenticated(
        context=context, resolved_object=resolved_object
    ):
        user = get_context_user(context=context)
        return not resolved_object.favorites.filter(user=user).exists()


link_document_favorites_add_multiple = Link(
    text=_(message='Add to favorites'),
    icon=icon_document_favorite_add_multiple,
    view='document_favorites:document_favorite_add_multiple'
)
link_document_favorites_add_single = Link(
    condition=condition_not_is_in_favorites,
    args='resolved_object.id', icon=icon_document_favorite_add_single,
    permission=permission_document_view, text=_(message='Add to favorites'),
    view='document_favorites:document_favorite_add'
)
link_document_favorites_list = Link(
    condition=condition_user_is_authenticated,
    icon=icon_document_favorite_list, text=_(message='Favorites'),
    view='document_favorites:document_favorite_list'
)
link_document_favorites_remove_multiple = Link(
    text=_(message='Remove from favorites'),
    icon=icon_document_favorite_remove_multiple,
    view='document_favorites:document_favorite_remove_multiple'
)
link_document_favorites_remove_single = Link(
    condition=condition_is_in_favorites,
    args='resolved_object.id', icon=icon_document_favorite_remove_single,
    permission=permission_document_view, text=_(
        message='Remove from favorites'
    ), view='document_favorites:document_favorite_remove'
)
