from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from actstream.models import Action

from mayan.apps.databases.classes import QuerysetParametersSerializer
from mayan.apps.organizations.utils import get_organization_installation_url
from mayan.apps.views.generics import ConfirmView
from mayan.apps.views.view_mixins import ExternalContentTypeObjectViewMixin

from ..icons import (
    icon_event_list_export, icon_object_event_list_export,
    icon_verb_event_list_export
)
from ..permissions import permission_events_export
from ..tasks import task_event_queryset_export

from .view_mixins import VerbEventViewMixin


class EventExportBaseView(ConfirmView):
    object_permission = permission_events_export
    view_icon = icon_event_list_export

    def get_extra_context(self):
        return {
            'message': _(
                message='The process will be performed in the background. '
                'The exported events will be available in the downloads '
                'area.'
            )
        }

    def view_action(self):
        decomposed_queryset = QuerysetParametersSerializer.decompose(
            _model=Action, **self.get_queryset_parameters()
        )

        task_event_queryset_export.apply_async(
            kwargs={
                'decomposed_queryset': decomposed_queryset,
                'organization_installation_url': get_organization_installation_url(
                    request=self.request
                ),
                'user_id': self.request.user.pk
            }
        )

        messages.success(
            message=_(
                message='Event list export task queued successfully.'
            ), request=self.request
        )


class EventListExportView(EventExportBaseView):
    object_permission = permission_events_export
    view_icon = icon_event_list_export

    def get_extra_context(self):
        context = super().get_extra_context()
        context.update(
            {
                'submit_label': _(message='Export'),
                'title': _(message='Export events')
            }
        )
        return context

    def get_queryset_parameters(self):
        return {'_method_name': 'all'}


class ObjectEventExportView(
    ExternalContentTypeObjectViewMixin, EventExportBaseView
):
    view_icon = icon_object_event_list_export

    def get_extra_context(self):
        context = super().get_extra_context()
        context.update(
            {
                'object': self.external_object,
                'submit_label': _(message='Export'),
                'title': _(
                    message='Export events of: %s'
                ) % self.external_object
            }
        )
        return context

    def get_queryset_parameters(self):
        return {'_method_name': 'any', 'obj': self.external_object}


class VerbEventExportView(VerbEventViewMixin, EventExportBaseView):
    view_icon = icon_verb_event_list_export

    def get_extra_context(self):
        context = super().get_extra_context()
        context.update(
            {
                'submit_label': _(message='Export'),
                'title': _(
                    message='Export events of type: %s'
                ) % self.event_type
            }
        )
        return context

    def get_queryset_parameters(self):
        return {'_method_name': 'filter', 'verb': self.event_type.id}
