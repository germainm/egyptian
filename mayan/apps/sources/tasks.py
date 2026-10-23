import logging

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import OperationalError

from mayan.apps.lock_manager.backends.base import LockingBackend
from mayan.apps.lock_manager.exceptions import LockError
from mayan.celery import app

from .exceptions import SourceActionExceptionRejected
from .literals import DEFAULT_SOURCES_LOCK_EXPIRE, ERROR_LOG_DOMAIN_NAME

logger = logging.getLogger(name=__name__)


@app.task(bind=True, ignore_result=True, retry_backoff=True)
def task_source_backend_action_background_task(
    self, action_name, source_id, action_interface_kwargs=None
):
    Source = apps.get_model(
        app_label='sources', model_name='Source'
    )

    action_interface_kwargs = action_interface_kwargs or {}

    try:
        source = Source.objects.get(pk=source_id)
        action = source.get_action(name=action_name)
    except OperationalError as exception:
        raise self.retry(exc=exception)

    try:
        action.background_task(
            interface_load_kwargs=action_interface_kwargs
        )
    except SourceActionExceptionRejected as exception:
        logger.warning(
            'Rejected input for source id: %s; %s', source_id, exception
        )
        source.error_log.create(
            domain_name=ERROR_LOG_DOMAIN_NAME, text=str(exception)
        )
    except Exception as exception:
        logger.error(
            'Error processing source id: %s; %s', source_id, exception,
            exc_info=True
        )
        source.error_log.create(
            domain_name=ERROR_LOG_DOMAIN_NAME,
            text='{}; {}'.format(
                exception.__class__.__name__, exception
            )
        )
        if settings.DEBUG:
            raise


@app.task(ignore_result=True)
def task_source_backend_action_execute(
    action_name, source_id, action_interface_kwargs=None, user_id=None
):
    Source = apps.get_model(
        app_label='sources', model_name='Source'
    )

    User = get_user_model()

    action_interface_kwargs = action_interface_kwargs or {}

    lock_id = 'task_source_backend_action_default_execute-%d' % source_id

    try:
        logger.debug('trying to acquire lock: %s', lock_id)
        lock = LockingBackend.get_backend().acquire_lock(
            name=lock_id, timeout=DEFAULT_SOURCES_LOCK_EXPIRE
        )
    except LockError:
        logger.debug('unable to obtain lock: %s' % lock_id)
    else:
        logger.debug('acquired lock: %s', lock_id)

        try:
            source = Source.objects.get(pk=source_id)

            if user_id:
                user = User.objects.get(pk=user_id)
            else:
                user = None

            action_interface_kwargs['user'] = user

            action = source.get_action(name=action_name)

            action.execute(
                interface_name='Model',
                interface_load_kwargs=action_interface_kwargs
            )
        except Exception as exception:
            logger.error(
                'Error processing source id: %s; %s', source_id, exception,
                exc_info=True
            )
            source.error_log.create(
                domain_name=ERROR_LOG_DOMAIN_NAME,
                text='{}; {}'.format(
                    exception.__class__.__name__, exception
                )
            )
            if settings.DEBUG:
                raise
        finally:
            lock.release()
