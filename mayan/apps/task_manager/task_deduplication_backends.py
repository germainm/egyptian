import logging
from datetime import timedelta

from django.apps import apps
from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .literals import TASK_DEDUPLICATION_ENTRY_STALE_DELETE_INTERVAL
from .settings import (
    setting_deduplication_queued_interval,
    setting_deduplication_stale_interval
)

logger = logging.getLogger(name=__name__)


class TaskDeduplicationBackend:
    label = None

    @classmethod
    def do_initialize(cls):
        if cls.__dict__.get('_is_initialized', False):
            return

        cls._is_initialized = True

        cls.initialize()

    @classmethod
    def get_deduplication_entry_model(cls):
        return apps.get_model(
            app_label='task_manager', model_name='TaskDeduplicationEntry'
        )

    @classmethod
    def initialize(cls):
        pass

    @classmethod
    def do_dispatch(cls, task, task_type, args, kwargs, options):
        raise NotImplementedError

    @classmethod
    def do_before_start(cls, task, task_type, args, kwargs):
        pass

    @classmethod
    def do_failure(cls, task, task_type, args, kwargs):
        pass

    @classmethod
    def do_success(cls, task, task_type, args, kwargs):
        pass


class TaskDeduplicationBackendNull(TaskDeduplicationBackend):
    label = _(message='No deduplication')

    @classmethod
    def do_dispatch(cls, task, task_type, args, kwargs, options):
        return task.do_apply_async(args=args, kwargs=kwargs, **options)


class TaskDeduplicationBackendMarkerMixin:
    @classmethod
    def do_before_start(cls, task, task_type, args, kwargs):
        TaskDeduplicationEntry = cls.get_deduplication_entry_model()

        key = task_type.get_deduplication_key(args=args, kwargs=kwargs)

        TaskDeduplicationEntry.objects.do_entry_start(
            dotted_path=task_type.dotted_path, key=key
        )

    @classmethod
    def do_dispatch(cls, task, task_type, args, kwargs, options):
        TaskDeduplicationEntry = cls.get_deduplication_entry_model()

        key = task_type.get_deduplication_key(args=args, kwargs=kwargs)

        must_dispatch = TaskDeduplicationEntry.objects.do_entry_create(
            dotted_path=task_type.dotted_path, key=key,
            queued_interval=setting_deduplication_queued_interval.value,
            stale_interval=setting_deduplication_stale_interval.value
        )

        if not must_dispatch:
            logger.debug(
                'Suppressed dispatch of task %s with key %s',
                task_type.dotted_path, key
            )

            return None

        cls.do_dispatch_schedule(
            args=args, key=key, kwargs=kwargs, options=options, task=task,
            task_type=task_type
        )

        return None

    @classmethod
    def do_dispatch_schedule(cls, task, task_type, args, key, kwargs, options):
        def do_task_publish():
            task.do_apply_async(args=args, kwargs=kwargs, **options)

        if settings.CELERY_TASK_ALWAYS_EAGER:
            do_task_publish()
        else:
            transaction.on_commit(func=do_task_publish)


class TaskDeduplicationBackendReleaseOnCompletion(
    TaskDeduplicationBackendMarkerMixin, TaskDeduplicationBackend
):
    label = _(message='Release on completion')

    @classmethod
    def initialize(cls):
        from .queues import task_type_deduplication_entry_stale_delete

        task_type_deduplication_entry_stale_delete.schedule = timedelta(
            seconds=TASK_DEDUPLICATION_ENTRY_STALE_DELETE_INTERVAL
        )

    @classmethod
    def do_failure(cls, task, task_type, args, kwargs):
        cls.do_release(
            args=args, kwargs=kwargs, task=task, task_type=task_type
        )

    @classmethod
    def do_release(cls, task, task_type, args, kwargs):
        TaskDeduplicationEntry = cls.get_deduplication_entry_model()

        key = task_type.get_deduplication_key(args=args, kwargs=kwargs)

        must_dispatch = TaskDeduplicationEntry.objects.do_entry_release(
            dotted_path=task_type.dotted_path, key=key
        )

        if must_dispatch:
            task.do_apply_async(args=args, kwargs=kwargs)

    @classmethod
    def do_success(cls, task, task_type, args, kwargs):
        cls.do_release(
            args=args, kwargs=kwargs, task=task, task_type=task_type
        )


class TaskDeduplicationBackendReleaseOnStart(
    TaskDeduplicationBackendMarkerMixin, TaskDeduplicationBackend
):
    label = _(message='Release on start')

    @classmethod
    def do_before_start(cls, task, task_type, args, kwargs):
        TaskDeduplicationEntry = cls.get_deduplication_entry_model()

        key = task_type.get_deduplication_key(args=args, kwargs=kwargs)

        TaskDeduplicationEntry.objects.do_entry_delete(
            dotted_path=task_type.dotted_path, key=key
        )


class TaskDeduplicationBackendReleaseOnDispatch(
    TaskDeduplicationBackendMarkerMixin, TaskDeduplicationBackend
):
    label = _(message='Release on dispatch')

    @classmethod
    def do_dispatch_schedule(cls, task, task_type, args, key, kwargs, options):
        TaskDeduplicationEntry = cls.get_deduplication_entry_model()

        TaskDeduplicationEntry.objects.do_entry_delete(
            dotted_path=task_type.dotted_path, key=key
        )

        def do_task_publish():
            task.do_apply_async(args=args, kwargs=kwargs, **options)

        transaction.on_commit(func=do_task_publish)


class TaskDeduplicationBackendManual(
    TaskDeduplicationBackendMarkerMixin, TaskDeduplicationBackend
):
    label = _(message='Manual release')
