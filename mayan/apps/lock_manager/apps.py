import logging
import sys
import uuid

from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig

from .backends.base import LockingBackend
from .literals import COMMAND_NAME_LOCK_MANAGER_PURGE_LOCKS, TEST_LOCK_NAME
from .settings import setting_backend

logger = logging.getLogger(name=__name__)


class LockManagerApp(MayanAppConfig):
    has_tests = True
    name = 'mayan.apps.lock_manager'
    verbose_name = _(message='Lock manager')

    def ready(self):
        super().ready()

        if COMMAND_NAME_LOCK_MANAGER_PURGE_LOCKS not in sys.argv:
            logger.info('Starting lock backend connectivity test')
            lock_name = '{}-{}'.format(
                TEST_LOCK_NAME, uuid.uuid4()
            )
            lock_instance = LockingBackend.get_backend()
            try:
                lock = lock_instance.acquire_lock(
                    name=lock_name, timeout=1
                )
            except Exception as exception:
                error_message = 'Error initializing the locking backend: {}; {}'.format(
                    setting_backend.value, exception
                )
                logger.critical(error_message)
                raise RuntimeError(error_message) from exception
            else:
                lock.release()
