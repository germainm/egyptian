import logging

from django.utils.translation import gettext_lazy as _, ngettext

from mayan.apps.documents.models.document_models import Document
from mayan.apps.documents.permissions import permission_document_view
from mayan.apps.documents.views.document_views import DocumentListView
from mayan.apps.views.exceptions import ActionError
from mayan.apps.views.generics import MultipleObjectConfirmActionView

from .icons import (
    icon_document_favorite_add_multiple, icon_document_favorite_list,
    icon_document_favorite_remove_multiple
)
from .models import FavoriteDocument
from .settings import setting_favorite_count

logger = logging.getLogger(name=__name__)


class FavoriteDocumentListView(DocumentListView):
    view_icon = icon_document_favorite_list

    def get_document_queryset(self):
        return FavoriteDocument.valid.get_for_user(user=self.request.user)

    def get_extra_context(self):
        context = super().get_extra_context()
        context.update(
            {
                'no_results_icon': icon_document_favorite_list,
                'no_results_text': _(
                    message='Favorited documents will be listed in this view. '
                    'Up to %(count)d documents can be favorited per user.'
                ) % {'count': setting_favorite_count.value},
                'no_results_title': _(message='There are no favorited documents'),
                'title': _(message='Favorites')
            }
        )
        return context


class FavoriteAddView(MultipleObjectConfirmActionView):
    object_permission = permission_document_view
    pk_url_kwarg = 'document_id'
    source_queryset = Document.valid.all()
    success_message = _(
        message='%(count)d document added to favorites.'
    )
    success_message_plural = _(
        message='%(count)d documents added to favorites.'
    )
    view_icon = icon_document_favorite_add_multiple

    def get_extra_context(self):
        context = {
            'title': ngettext(
                singular='Add the selected document to favorites?',
                plural='Add the selected documents to favorites?',
                number=self.object_list.count()
            )
        }

        if self.object_list.count() == 1:
            context['object'] = self.object_list.first()

        return context

    def object_action(self, form, instance):
        FavoriteDocument.valid.add_for_user(
            document=instance, user=self.request.user
        )


class FavoriteRemoveView(MultipleObjectConfirmActionView):
    error_message = _(message='Document "%(instance)s" is not in favorites.')
    object_permission = permission_document_view
    pk_url_kwarg = 'document_id'
    source_queryset = Document.valid.all()
    success_message = _(
        message='%(count)d document removed from favorites.'
    )
    success_message_plural = _(
        message='%(count)d documents removed from favorites.'
    )
    view_icon = icon_document_favorite_remove_multiple

    def get_extra_context(self):
        context = {
            'title': ngettext(
                singular='Remove the selected document from favorites?',
                plural='Remove the selected documents from favorites?',
                number=self.object_list.count()
            )
        }

        if self.object_list.count() == 1:
            context['object'] = self.object_list.first()

        return context

    def object_action(self, form, instance):
        try:
            FavoriteDocument.valid.remove_for_user(
                document=instance, user=self.request.user
            )
        except FavoriteDocument.DoesNotExist:
            raise ActionError
