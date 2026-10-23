from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from mayan.apps.views.generics import (
    ConfirmView, SimpleView, SingleObjectListView
)

from .classes import StatisticNamespace
from .icons import (
    icon_statistic_detail, icon_statistic_namespace_detail,
    icon_statistic_namespace_list, icon_statistic_queue
)
from .permissions import permission_statistics_view
from .tasks import task_execute_statistic
from .view_mixins import StatisticTypeViewMixin


class StatisticNamespaceListView(SingleObjectListView):
    extra_context = {
        'hide_link': True,
        'no_results_icon': icon_statistic_namespace_list,
        'no_results_text': _(
            message='Statistics namespaces group statistics into logical '
            'units.'
        ),
        'no_results_title': _(message='No statistic namespaces available'),
        'title': _(message='Statistics namespaces')
    }
    template_name = 'appearance/list.html'
    view_icon = icon_statistic_namespace_list
    view_permission = permission_statistics_view

    def get_source_queryset(self):
        return StatisticNamespace.get_all()


class StatisticNamespaceDetailView(SingleObjectListView):
    view_icon = icon_statistic_namespace_detail
    view_permission = permission_statistics_view

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request=request, *args, **kwargs)

    def get_extra_context(self):
        return {
            'hide_link': True,
            'no_results_icon': icon_statistic_namespace_detail,
            'no_results_text': _(
                message='Statistics are metrics and chart representations of '
                'existing data.'
            ),
            'no_results_title': _(message='No statistic available'),
            'object': self.object,
            'title': _(message='Namespace details for: %s') % self.object
        }

    def get_object(self):
        return StatisticNamespace.get(
            slug=self.kwargs['slug']
        )

    def get_source_queryset(self):
        return self.object.statistics


class StatisticTypeDetailView(StatisticTypeViewMixin, SimpleView):
    view_icon = icon_statistic_detail
    view_permission = permission_statistics_view

    def get_extra_context(self):
        return {
            'chart_context': self.object.get_chart_context(),
            'namespace': self.object.namespace,
            'navigation_object_list': ('namespace', 'object'),
            'no_data': not self.object.get_results_data()['series'],
            'object': self.object,
            'title': _(message='Results for: %s') % self.object
        }

    def get_template_names(self):
        return (self.object.renderer.template_name,)


class StatisticTypeQueueView(StatisticTypeViewMixin, ConfirmView):
    view_icon = icon_statistic_queue
    view_permission = permission_statistics_view

    def get_extra_context(self):
        return {
            'namespace': self.object.namespace,
            'navigation_object_list': ('namespace', 'object'),
            'object': self.object,
            'submit_label': _(message='Queue'),
            'title': _(
                message='Queue statistic "%s" to be updated?'
            ) % self.object
        }

    def view_action(self):
        task_execute_statistic.delay(slug=self.object.slug)
        messages.success(
            message=_(
                message='Statistic "%s" queued successfully for update.'
            ) % self.object.label, request=self.request
        )
