import logging

from celery import Task

from .classes import TaskType

logger = logging.getLogger(name=__name__)


class DeduplicatedTask(Task):
    def do_apply_async(self, args=None, kwargs=None, **options):
        return super().apply_async(args=args, kwargs=kwargs, **options)

    def get_is_retry(self, options):
        request_id = getattr(self.request, 'id', None)

        if request_id is None:
            return False

        return options.get('task_id') == request_id

    def get_task_type(self):
        try:
            return TaskType.get(name=self.name)
        except KeyError:
            logger.debug(
                'No task type registered for the task named %s', self.name
            )

            return None

    def apply_async(self, args=None, kwargs=None, **options):
        task_type = self.get_task_type()

        if task_type is None:
            return self.do_apply_async(args=args, kwargs=kwargs, **options)

        if self.get_is_retry(options=options):
            return self.do_apply_async(args=args, kwargs=kwargs, **options)

        deduplication_backend = task_type.deduplication_backend

        return deduplication_backend.do_dispatch(
            args=args, kwargs=kwargs, options=options, task=self,
            task_type=task_type
        )

    def before_start(self, task_id, args, kwargs):
        task_type = self.get_task_type()

        if task_type is not None:
            deduplication_backend = task_type.deduplication_backend

            deduplication_backend.do_before_start(
                args=args, kwargs=kwargs, task=self, task_type=task_type
            )

        return super().before_start(
            args=args, kwargs=kwargs, task_id=task_id
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        task_type = self.get_task_type()

        if task_type is not None:
            deduplication_backend = task_type.deduplication_backend

            deduplication_backend.do_failure(
                args=args, kwargs=kwargs, task=self, task_type=task_type
            )

        return super().on_failure(
            args=args, einfo=einfo, exc=exc, kwargs=kwargs, task_id=task_id
        )

    def on_success(self, retval, task_id, args, kwargs):
        task_type = self.get_task_type()

        if task_type is not None:
            deduplication_backend = task_type.deduplication_backend

            deduplication_backend.do_success(
                args=args, kwargs=kwargs, task=self, task_type=task_type
            )

        return super().on_success(
            args=args, kwargs=kwargs, retval=retval, task_id=task_id
        )

