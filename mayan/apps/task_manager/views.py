from django.http import Http404
from django.utils.translation import gettext_lazy as _

from mayan.apps.views.generics import SingleObjectListView

from .classes import CeleryQueue, TaskType, Worker
from .icons import (
    icon_task_type_list, icon_worker_list, icon_worker_queue_list
)
from .permissions import permission_task_view


class TaskTypeListView(SingleObjectListView):
    view_icon = icon_task_type_list
    view_permission = permission_task_view

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_task_type_list,
            'no_results_text': _(
                message='Task types are the background operations the system '
                'can perform asynchronously.'
            ),
            'no_results_title': _(message='No task types available'),
            'title': _(message='Task types')
        }

    def get_source_queryset(self):
        return self.get_task_list()

    def get_task_list(self):
        return list(
            TaskType.all(sort_by='dotted_path')
        )


class QueueTaskTypeListView(TaskTypeListView):
    def get_extra_context(self):
        context = super().get_extra_context()

        queue = self.get_queue()

        context.update(
            {
                'object': queue,
                'worker': queue.worker,
                'navigation_object_list': ('worker', 'object'),
                'title': _(message='Task types for queue: %s') % queue
            }
        )

        return context

    def get_queue(self):
        try:
            return CeleryQueue.get(
                queue_name=self.kwargs['queue_name']
            )
        except KeyError:
            raise Http404(
                _(message='Queue: %s, not found') % self.kwargs['queue_name']
            )

    def get_task_list(self):
        queue = self.get_queue()

        return queue.task_types


class WorkerListView(SingleObjectListView):
    extra_context = {
        'hide_object': True,
        'no_results_icon': icon_worker_list,
        'no_results_text': _(
            message='Workers are the background processes that execute '
            'queued tasks.'
        ),
        'no_results_title': _(message='No workers available'),
        'title': _(message='Background task workers')
    }
    view_icon = icon_worker_list
    view_permission = permission_task_view

    def get_source_queryset(self):
        return Worker.all()


class WorkerQueueListView(SingleObjectListView):
    view_icon = icon_worker_queue_list
    view_permission = permission_task_view

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_worker_queue_list,
            'no_results_text': _(
                message='Queues group the task types processed by a worker.'
            ),
            'no_results_title': _(message='No queues available'),
            'object': self.get_worker(),
            'title': _(message='Queues for worker: %s') % self.get_worker()
        }

    def get_worker(self):
        try:
            return Worker.get(
                name=self.kwargs['worker_name']
            )
        except KeyError:
            raise Http404(
                _(message='Worker: %s, not found') % self.kwargs['worker_name']
            )

    def get_source_queryset(self):
        return self.get_worker().queues
