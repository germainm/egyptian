import logging

from django.contrib import messages
from django.template import RequestContext
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.views.generics import (
    ConfirmView, MultipleObjectConfirmActionView, MultipleObjectDeleteView,
    SingleObjectCreateView, SingleObjectDetailView, SingleObjectListView
)

from .forms import MessageCreateForm, MessageDetailForm
from .icons import (
    icon_message_create, icon_message_delete, icon_message_detail,
    icon_message_list, icon_message_mark_read, icon_message_mark_read_all,
    icon_message_mark_unread
)
from .links import link_message_create
from .models import Message
from .permissions import (
    permission_message_create, permission_message_delete,
    permission_message_edit, permission_message_view
)

logger = logging.getLogger(name=__name__)


class MessageCreateView(SingleObjectCreateView):
    form_class = MessageCreateForm
    model = Message
    view_icon = icon_message_create
    view_permission = permission_message_create

    def get_extra_context(self):
        return {
            'title': _(message='Create message')
        }

    def get_instance_extra_data(self):
        return {
            '_event_actor': self.request.user,
            'sender_object': self.request.user
        }


class MessageDeleteView(MultipleObjectDeleteView):
    error_message = _(
        message='Error deleting message "%(instance)s"; %(exception)s'
    )
    object_permission = permission_message_delete
    pk_url_kwarg = 'message_id'
    post_action_redirect = reverse_lazy(viewname='messaging:message_list')
    success_message_plural = _(
        message='%(count)d messages deleted successfully.'
    )
    success_message_single = _(
        message='Message "%(object)s" deleted successfully.'
    )
    success_message_singular = _(
        message='%(count)d message deleted successfully.'
    )
    title_plural = _(message='Delete the %(count)d selected messages.')
    title_single = _(message='Delete message: %(object)s.')
    title_singular = _(message='Delete the %(count)d selected message.')
    view_icon = icon_message_delete

    def get_source_queryset(self):
        return self.request.user.messages.all()


class MessageDetailView(SingleObjectDetailView):
    form_class = MessageDetailForm
    object_permission = permission_message_view
    pk_url_kwarg = 'message_id'
    view_icon = icon_message_detail

    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request=request, *args, **kwargs)
        self.object._event_actor = self.request.user
        self.object.mark_read(user=self.request.user)
        return result

    def get_extra_context(self):
        return {
            'form_hide_help_text': True,
            'hide_labels': True,
            'object': self.object,
            'title': _(message='Details of message: %s') % self.object
        }

    def get_initial(self):
        return {
            'body': self.object.get_rendered_body()
        }

    def get_source_queryset(self):
        return self.request.user.messages.all()


class MessageListView(SingleObjectListView):
    object_permission = permission_message_view
    view_icon = icon_message_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_message_list,
            'no_results_main_link': link_message_create.resolve(
                context=RequestContext(request=self.request)
            ),
            'no_results_text': _(
                message='Here you will find text messages from other users '
                'or from the system.'
            ),
            'no_results_title': _(message='There are no messages'),
            'title': _(message='Messages')
        }

    def get_source_queryset(self):
        return self.request.user.messages.all()


class MessageMarkReadView(MultipleObjectConfirmActionView):
    error_message = _(
        message='Error marking message "%(instance)s" as read; %(exception)s'
    )
    object_permission = permission_message_edit
    pk_url_kwarg = 'message_id'
    post_action_redirect = reverse_lazy(viewname='messaging:message_list')
    success_message_plural = _(
        message='%(count)d messages marked as read successfully.'
    )
    success_message_single = _(
        message='Message "%(object)s" marked as read successfully.'
    )
    success_message_singular = _(
        message='%(count)d message marked as read successfully.'
    )
    title_plural = _(message='Mark the %(count)d selected messages as read.')
    title_single = _(message='Mark the message "%(object)s" as read.')
    title_singular = _(message='Mark the %(count)d selected message as read.')
    view_icon = icon_message_mark_read

    def get_extra_context(self):
        context = {
            'submit_label': _(message='Mark as read')
        }

        if self.object_list.count() == 1:
            context.update(
                {
                    'object': self.object_list.first()
                }
            )

        return context

    def get_source_queryset(self):
        return self.request.user.messages.all()

    def object_action(self, instance, form=None):
        instance.mark_read(user=self.request.user)


class MessageMarkReadAllView(ConfirmView):
    object_permission = permission_message_edit
    post_action_redirect = reverse_lazy(viewname='messaging:message_list')
    view_icon = icon_message_mark_read_all

    def get_extra_context(self):
        return {
            'submit_label': _(message='Mark as read'),
            'title': _(message='Mark all message as read?')
        }

    def get_source_queryset(self):
        return self.request.user.messages.all()

    def view_action(self, form=None):
        queryset = self.get_queryset()

        for message in queryset.all():
            message.mark_read(user=self.request.user)

        messages.success(
            message=_(message='All messages marked as read.'),
            request=self.request
        )


class MessageMarkUnReadView(MultipleObjectConfirmActionView):
    error_message = _(
        message='Error marking message "%(instance)s" as unread; '
        '%(exception)s'
    )
    object_permission = permission_message_edit
    pk_url_kwarg = 'message_id'
    post_action_redirect = reverse_lazy(viewname='messaging:message_list')
    success_message_plural = _(
        message='%(count)d messages marked as unread successfully.'
    )
    success_message_single = _(
        message='Message "%(object)s" marked as unread successfully.'
    )
    success_message_singular = _(
        message='%(count)d message marked as unread successfully.'
    )
    title_plural = _(message='Mark the %(count)d selected messages as unread.')
    title_single = _(message='Mark the message "%(object)s" as unread.')
    title_singular = _(message='Mark the %(count)d selected message as unread.')
    view_icon = icon_message_mark_unread

    def get_extra_context(self):
        context = {
            'submit_label': _(message='Mark as unread')
        }

        if self.object_list.count() == 1:
            context.update(
                {
                    'object': self.object_list.first()
                }
            )

        return context

    def get_source_queryset(self):
        return self.request.user.messages.all()

    def object_action(self, instance, form=None):
        instance.mark_unread(user=self.request.user)
