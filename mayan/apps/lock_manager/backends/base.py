import logging
import threading

from django.utils.module_loading import import_string

from ..settings import setting_backend, setting_default_lock_timeout

lock_initialize = threading.Lock()
logger = logging.getLogger(name=__name__)


class LockingBackend:
    _is_initialized = False

    @classmethod
    def _initialize(cls):
        return

    @classmethod
    def _do_initialize(cls):
        if cls._is_initialized:
            return

        with lock_initialize:
            if not cls._is_initialized:
                cls._initialize()
                cls._is_initialized = True

    @staticmethod
    def get_backend():
        return import_string(dotted_path=setting_backend.value)

    @classmethod
    def acquire_lock(cls, name, timeout=None):
        timeout = timeout or setting_default_lock_timeout.value
        logger.debug('acquiring lock: %s, timeout: %s', name, timeout)
        return cls._acquire_lock(name=name, timeout=timeout)

    @classmethod
    def purge_locks(cls):
        cls._do_initialize()

        logger.debug(msg='purging locks')
        return cls._purge_locks()

    def __init__(self, *args, **kwargs):
        self.__class__._do_initialize()

        return self._init(*args, **kwargs)

    def release(self):
        logger.debug('releasing lock: %s', self.name)
        return self._release()
