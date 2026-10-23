import logging

from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.models import AccessControlList
from mayan.apps.common.settings import setting_home_view
from mayan.apps.views.generics import (
    ConfirmView, MultipleObjectConfirmActionView
)

from ..icons import (
    icon_document_trash_multiple, icon_trash_can_empty,
    icon_trashed_document_delete_multiple, icon_trashed_document_list,
    icon_trashed_document_restore_multiple
)
from ..models.document_models import Document
from ..models.trashed_document_models import TrashedDocument
from ..permissions import (
    permission_document_trash, permission_document_view,
    permission_trash_empty, permission_trashed_document_delete,
    permission_trashed_document_restore
)
from ..tasks import (
    task_document_move_to_trash, task_trash_can_empty,
    task_trashed_document_delete
)

from .document_views import DocumentListView

logger = logging.getLogger(name=__name__)


class DocumentTrashView(MultipleObjectConfirmActionView):
    object_permission = permission_document_trash
    pk_url_kwarg = 'document_id'
    source_queryset = Document.valid.all()
    success_message_single = _(
        message='Document "%(object)s" queued for trashing.'
    )
    success_message_singular = _(
        message='%(count)d documents queued for trashing.'
    )
    success_message_plural = _(
        message='%(count)d documents queued for trashing.'
    )
    title_single = _(message='Move the document "%(object)s" to trash?')
    title_singular = _(message='Move the selected document to the trash?')
    title_plural = _(
        message='Move the %(count)d selected documents to trash?'
    )
    view_icon = icon_document_trash_multiple

    def get_extra_context(self):
        context = {
            'submit_label': _(message='Move to trash')
        }

        if self.object_list.count() == 1:
            context['object'] = self.object_list.first()

        return context

    def get_post_action_redirect(self):
        if 'document_id' in self.kwargs:
            return reverse(viewname=setting_home_view.value)
        else:
            return None

    def object_action(self, form, instance):
        task_document_move_to_trash.apply_async(
            kwargs={
                'document_id': instance.pk, 'user_id': self.request.user.pk
            }
        )


class EmptyTrashCanView(ConfirmView):
    action_cancel_redirect = post_action_redirect = reverse_lazy(
        'documents:document_list_deleted'
    )
    extra_context = {
        'title': _(message='Empty trash?')
    }
    view_icon = icon_trash_can_empty
    view_permission = permission_trash_empty

    def view_action(self):
        task_trash_can_empty.apply_async(
            kwargs={
                'user_id': self.request.user.pk
            }
        )

        messages.success(
            message=_(message='The trash emptying task has been queued.'),
            request=self.request
        )


class TrashedDocumentDeleteView(MultipleObjectConfirmActionView):
    model = TrashedDocument
    object_permission = permission_trashed_document_delete
    pk_url_kwarg = 'document_id'
    success_message_plural = _(
        message='%(count)d trashed documents submitted for deletion.'
    )
    success_message_single = _(
        message='Trash document "%(object)s" submitted for deletion.'
    )
    success_message_singular = _(
        message='%(count)d trashed document submitted for deletion.'
    )
    title_plural = _(message='Delete the %(count)d selected trashed documents?')
    title_single = _(message='Delete the trashed document "%(object)s"?')
    title_singular = _(message='Delete the selected trashed document?')
    view_icon = icon_trashed_document_delete_multiple

    def get_extra_context(self):
        context = {}

        if self.object_list.count() == 1:
            context['object'] = self.object_list.first()

        return context

    def object_action(self, form, instance):
        task_trashed_document_delete.apply_async(
            kwargs={
                'trashed_document_id': instance.pk,
                'user_id': self.request.user.pk
            }
        )


class TrashedDocumentListView(DocumentListView):
    object_permission = None
    view_icon = icon_trashed_document_list

    def get_document_queryset(self):
        return AccessControlList.objects.restrict_queryset(
            permission=permission_document_view,
            queryset=TrashedDocument.trash.all(),
            user=self.request.user
        )

    def get_extra_context(self):
        context = super().get_extra_context()
        context.update(
            {
                'hide_link': True,
                'no_results_icon': icon_trashed_document_list,
                'no_results_text': _(
                    message='To avoid loss of data, documents are not deleted '
                    'instantly. First, they are placed in the trash can. '
                    'From here they can be then finally deleted or restored.'
                ),
                'no_results_title': _(
                    message='There are no documents in the trash can'
                ),
                'title': _(message='Documents in trash')
            }
        )
        return context


class TrashedDocumentRestoreView(MultipleObjectConfirmActionView):
    model = TrashedDocument
    object_permission = permission_trashed_document_restore
    pk_url_kwarg = 'document_id'
    success_message_plural = _(
        message='%(count)d trashed documents restored.'
    )
    success_message_single = _(
        message='Trashed document "%(object)s" restored.'
    )
    success_message_singular = _(
        message='%(count)d trashed document restored.'
    )
    title_plural = _(message='Restore the %(count)d selected trashed documents?')
    title_single = _(message='Restore the trashed document: %(object)s')
    title_singular = _(message='Restore the selected trashed document?')
    view_icon = icon_trashed_document_restore_multiple

    def get_extra_context(self):
        context = {
            'submit_label': _(message='Restore')
        }

        if self.object_list.count() == 1:
            context['object'] = self.object_list.first()

        return context

    def object_action(self, form, instance):
        instance.restore(user=self.request.user)
