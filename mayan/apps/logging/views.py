from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from mayan.apps.views.generics import (
    ConfirmView, SingleObjectDeleteView, SingleObjectListView
)
from mayan.apps.views.view_mixins import ExternalContentTypeObjectViewMixin

from .icons import (
    icon_global_error_log_entry_list, icon_object_errors,
    icon_object_error_log_entry_delete, icon_object_error_log_entry_list,
    icon_object_error_log_entry_list_clear
)
from .models import GlobalErrorLogPartitionEntry
from .permissions import (
    permission_error_log_entry_delete, permission_error_log_entry_view
)


class GlobalErrorLogEntryList(SingleObjectListView):
    model = GlobalErrorLogPartitionEntry
    object_permission = permission_error_log_entry_view
    view_icon = icon_global_error_log_entry_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_object_errors,
            'no_results_text': _(
                message='This view displays the error log of different '
                'objects. An empty list is a good thing.'
            ),
            'no_results_title': _(
                message='There are no error log entries'
            ),
            'title': _(message='Global error log')
        }


class ObjectErrorLogEntryListClearView(
    ExternalContentTypeObjectViewMixin, ConfirmView
):
    external_object_permission = permission_error_log_entry_delete
    view_icon = icon_object_error_log_entry_list_clear

    def get_extra_context(self):
        return {
            'object': self.external_object,
            'title': _(
                message='Clear error log entries for: %s'
            ) % self.external_object
        }

    def view_action(self):
        self.external_object.error_log.clear(user=self.request.user)
        messages.success(
            message=_(message='Object error log cleared successfully'),
            request=self.request
        )


class ObjectErrorLogEntryDeleteView(
    ExternalContentTypeObjectViewMixin, SingleObjectDeleteView
):
    external_object_permission = permission_error_log_entry_delete
    object_permission = permission_error_log_entry_delete
    pk_url_kwarg = 'error_log_partition_entry_id'
    view_icon = icon_object_error_log_entry_delete

    def get_extra_context(self):
        return {
            'external_object': self.external_object,
            'navigation_object_list': ('external_object', 'object'),
            'title': _(message='Delete error log entry: %s') % self.object
        }

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}

    def get_source_queryset(self):
        return self.external_object.error_log.all()


class ObjectErrorLogEntryListView(
    ExternalContentTypeObjectViewMixin, SingleObjectListView
):
    external_object_permission = permission_error_log_entry_view
    view_icon = icon_object_error_log_entry_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_object_errors,
            'no_results_text': _(
                message='This view displays the error log of an object. '
                'An empty list is a good thing.'
            ),
            'no_results_title': _(
                message='There are no error log entries'
            ),
            'object': self.external_object,
            'subtitle': _(
                message='Maximum number of entries kept for this object '
                'type: %s'
            ) % self.external_object.error_log_instance.limit,
            'title': _(
                message='Error log entries for: %s'
            ) % self.external_object
        }

    def get_source_queryset(self):
        return self.external_object.error_log.all()
