import json
import logging

from kombu import Exchange, Queue

from django.core.exceptions import ImproperlyConfigured
from django.template.defaultfilters import filesizeformat
from django.urls import reverse
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.class_mixins import AppsModuleLoaderMixin
from mayan.apps.common.exceptions import NonUniqueError
from mayan.celery import app as celery_app

from .literals import WORKER_DEFAULT_CONCURRENCY
from .settings import setting_deduplication_backend_map
from .task_deduplication_backends import TaskDeduplicationBackendNull

logger = logging.getLogger(name=__name__)


class TaskType:
    _registry = {}

    @classmethod
    def all(cls, sort_by=None):
        values = list(
            cls._registry.values()
        )

        if sort_by:
            values.sort(
                key=lambda entry: getattr(entry, sort_by)
            )

        return values

    @classmethod
    def get(cls, name):
        return cls._registry[name]

    def __init__(
        self, dotted_path, label, deduplication_backend=None, name=None,
        schedule=None
    ):
        self.deduplication_backend = deduplication_backend or TaskDeduplicationBackendNull
        self.dotted_path = dotted_path
        self.label = label
        self.name = name or dotted_path.split('.')[-1]
        self.schedule = schedule
        self.queue = None
        self.__class__._registry[self.dotted_path] = self

    def __str__(self):
        return str(self.label)

    def do_deduplication_backend_override(self):
        backend_map = setting_deduplication_backend_map.value or {}

        dotted_path = backend_map.get(self.dotted_path)

        if not dotted_path:
            return

        try:
            deduplication_backend = import_string(dotted_path=dotted_path)
        except ImportError as exception:
            raise ImproperlyConfigured(
                'Unable to import the deduplication strategy `{}` '
                'requested for the task type `{}`; {}'.format(
                    dotted_path, self.dotted_path, exception
                )
            ) from exception

        self.deduplication_backend = deduplication_backend

    def get_deduplication_backend_label(self):
        return self.deduplication_backend.label

    get_deduplication_backend_label.help_text = _(
        message='Strategy deciding whether a request to perform this task '
        'is dispatched or collapsed into a request already outstanding.'
    )
    get_deduplication_backend_label.short_description = _(
        message='Deduplication'
    )

    def get_deduplication_key(self, args=None, kwargs=None):
        data = {
            'args': list(args or ()),
            'kwargs': kwargs or {}
        }

        return json.dumps(default=str, obj=data, sort_keys=True)

    def get_dotted_path(self):
        return self.dotted_path

    get_dotted_path.help_text = _(message='The Python path to the task code.')
    get_dotted_path.short_description = _(message='Dotted path')

    def get_label(self):
        return self.label

    get_label.help_text = _(
        message='Human readable description of the task type.'
    )
    get_label.short_description = _(message='Label')

    def get_name(self):

        return self.name

    get_name.help_text = _(message='Unique internal name of the task type.')
    get_name.short_description = _(message='Name')

    def get_queue(self):

        return self.queue

    get_queue.short_description = _(message='Queue')

    def get_schedule(self):
        return self.schedule

    get_schedule.help_text = _(
        message='Trigger interval if the task type is set for periodic '
        'execution.'
    )
    get_schedule.short_description = _(message='Schedule')

    def get_worker(self):
        if self.queue:
            return self.queue.worker

        return None

    get_worker.short_description = _(message='Worker')

    def validate(self):
        try:
            import_string(dotted_path=self.dotted_path)
        except Exception as exception:
            logger.critical(
                'Exception validating task %s; %s', self.label, exception,
                exc_info=True
            )
            raise


class Task:
    def __init__(self, task_type, kwargs):
        self.task_type = task_type
        self.kwargs = kwargs

    def __str__(self):
        return str(self.task_type)


class CeleryQueue(AppsModuleLoaderMixin):
    _loader_module_name = 'queues'
    _registry = {}
    _registry_task_types = {}

    @classmethod
    def all(cls):
        return sorted(
            cls._registry.values(), key=lambda instance: instance.label
        )

    @classmethod
    def get(cls, queue_name):
        return cls._registry[queue_name]

    @classmethod
    def post_load_modules(cls):
        for task_type in TaskType.all():
            task_type.do_deduplication_backend_override()

        deduplication_backend_list = []

        for task_type in TaskType.all():
            deduplication_backend = task_type.deduplication_backend

            if deduplication_backend not in deduplication_backend_list:
                deduplication_backend_list.append(deduplication_backend)

        for deduplication_backend in deduplication_backend_list:
            deduplication_backend.do_initialize()

        for task_type in TaskType.all():
            task_type.validate()

        CeleryQueue.update_celery()

        for task_name, task in celery_app.tasks.items():
            if not task_name.startswith('celery') and task_name not in cls._registry_task_types:
                raise ImproperlyConfigured(
                    'Task `{}` is not properly configured and/or missing '
                    'from the queue definition.'.format(task_name)
                )

    @classmethod
    def update_celery(cls):
        for instance in cls.all():
            instance._update_celery()

    def __init__(
        self, name, label, worker, default_queue=False, transient=False
    ):
        self.default_queue = default_queue
        self.label = label
        self.name = name
        self.transient = transient
        self.task_types = []
        self.worker = worker

        if name in self.__class__._registry:
            raise NonUniqueError(
                'A queue named `{}`, already exists.'.format(name)
            )

        self.__class__._registry[name] = self
        worker._queues.append(self)

    def __str__(self):
        return str(self.label)

    def _update_celery(self):
        kwargs = {
            'exchange': Exchange(self.name), 'name': self.name,
            'routing_key': self.name
        }

        if self.transient:
            kwargs['delivery_mode'] = 1

        queue_new = Queue(**kwargs)
        if queue_new not in celery_app.conf.task_queues:
            celery_app.conf.task_queues.append(queue_new)

        if self.default_queue:
            celery_app.conf.task_default_queue = self.name

        for task_type in self.task_types:
            celery_app.conf.task_routes.update(
                {
                    task_type.dotted_path: {
                        'queue': self.name
                    }
                }
            )

            if task_type.schedule:
                celery_app.conf.beat_schedule.update(
                    {
                        task_type.name: {
                            'schedule': task_type.schedule,
                            'task': task_type.dotted_path
                        }
                    }
                )

    def get_absolute_url(self):
        return reverse(
            kwargs={'queue_name': self.name},
            viewname='task_manager:queue_task_type_list'
        )

    def add_task_type(self, *args, **kwargs):
        task_type = TaskType(*args, **kwargs)
        self.task_types.append(task_type)
        self.__class__._registry_task_types[task_type.dotted_path] = self
        task_type.queue = self
        return task_type

    def get_task_type_count(self):
        return len(self.task_types)

    get_task_type_count.help_text = _(
        message='Number of task types managed by the queue.'
    )
    get_task_type_count.short_description = _(message='Task type count')

    def remove(self):
        kwargs = {
            'name': self.name, 'exchange': Exchange(self.name),
            'routing_key': self.name
        }

        if self.transient:
            kwargs['delivery_mode'] = 1

        queue = Queue(**kwargs)
        if queue in celery_app.conf.task_queues:
            celery_app.conf.task_queues.remove(queue)

        if self.default_queue:
            celery_app.conf.task_default_queue = None

        for task_type in self.task_types:
            celery_app.conf.task_routes.pop(task_type.dotted_path, None)

            if task_type.schedule:
                celery_app.conf.beat_schedule.pop(task_type.name, None)

        self.__class__._registry.pop(self.name, None)
        if self in self.worker._queues:
            self.worker._queues.remove(self)

    @property
    def verbose_name(self):
        return _(message='Queue')


class Worker:
    _registry = {}

    @classmethod
    def all(cls):
        return sorted(
            cls._registry.values(), key=lambda instance: instance.name
        )

    @classmethod
    def get(cls, name):
        return cls._registry[name]

    @classmethod
    def get_default(cls):
        for worker in cls._registry.values():
            if worker.default_worker:
                return worker

        raise ImproperlyConfigured(
            'No worker has been flagged as the default worker.'
        )

    def __init__(
        self, name, default_worker=False, description=None,
        maximum_memory_per_child=None, maximum_tasks_per_child=None,
        concurrency=None, label=None, nice_level=0
    ):
        self.concurrency = concurrency or WORKER_DEFAULT_CONCURRENCY
        self.default_worker = default_worker
        self.description = description
        self._label = label
        self.maximum_memory_per_child = maximum_memory_per_child
        self.maximum_tasks_per_child = maximum_tasks_per_child
        self.name = name
        self.nice_level = nice_level
        self._queues = []
        self.__class__._registry[name] = self

    def __str__(self):
        return str(self.label)

    def get_absolute_url(self):
        return reverse(
            kwargs={'worker_name': self.name},
            viewname='task_manager:worker_queue_list'
        )

    def get_maximum_memory_per_child(self):
        return filesizeformat(bytes_=self.maximum_memory_per_child)

    get_maximum_memory_per_child.help_text = _(
        message='Maximum amount of resident memory a worker can execute '
        'before it\'s replaced by a new process.'
    )
    get_maximum_memory_per_child.short_description = _(
        message='Maximum memory per child'
    )

    def get_queue_count(self):
        return len(self._queues)

    get_queue_count.short_description = _(message='Queue count')

    def get_task_type_count(self):
        result = 0
        for queue in self._queues:
            result += queue.get_task_type_count()

        return result

    get_task_type_count.help_text = _(
        message='Number of task types managed by the worker.'
    )
    get_task_type_count.short_description = _(message='Task type count')

    @property
    def label(self):
        return self._label or self.name

    @property
    def queues(self):
        return sorted(self._queues, key=lambda queue: queue.name)

    @property
    def verbose_name(self):
        return _(message='Worker')
