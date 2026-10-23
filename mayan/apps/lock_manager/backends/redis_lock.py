import logging

import redis

from mayan.apps.dependencies.exceptions import DependenciesException

from ..exceptions import LockBackendError, LockError
from ..settings import setting_backend_arguments

from .base import LockingBackend
from .literals import (
    REDIS_LOCK_NAME_PREFIX, REDIS_LOCK_VERSION_REQUIRED,
    REDIS_SCAN_CURSOR_INITIAL, REDIS_SCAN_KEYS_COUNT
)

logger = logging.getLogger(name=__name__)


class RedisLock(LockingBackend):
    _connection_pool = None
    _server = None

    @classmethod
    def _acquire_lock(cls, name, timeout):
        return RedisLock(name=name, timeout=timeout)

    @classmethod
    def _initialize(cls):
        if redis.VERSION < REDIS_LOCK_VERSION_REQUIRED:
            raise DependenciesException(
                'The Redis lock backend requires the Redis Python client '
                'version {} or later.'.format(
                    '.'.join(
                        map(str, REDIS_LOCK_VERSION_REQUIRED)
                    )
                )
            )

        backend_arguments = setting_backend_arguments.value

        redis_url = backend_arguments.get('redis_url', None)

        if not redis_url:
            raise LockBackendError(
                'The Redis lock backend requires the `redis_url` backend '
                'argument. Add it to the `LOCK_MANAGER_BACKEND_ARGUMENTS` '
                'setting.'
            )

        kwargs = {'url': redis_url}

        max_connections = backend_arguments.get('max_connections', None)

        if max_connections:
            kwargs['max_connections'] = max_connections

        try:
            cls._connection_pool = redis.ConnectionPool.from_url(**kwargs)
        except (ValueError, redis.exceptions.RedisError) as exception:
            raise LockBackendError(
                'Error setting up the Redis connection pool; {}'.format(
                    exception
                )
            ) from exception

        cls._server = redis.Redis(connection_pool=cls._connection_pool)

    @classmethod
    def get_redis_connection(cls):
        cls._do_initialize()

        return cls._server

    @classmethod
    def _purge_locks(cls):
        server = cls.get_redis_connection()

        cursor = REDIS_SCAN_CURSOR_INITIAL
        match = '{}*'.format(REDIS_LOCK_NAME_PREFIX)

        try:
            while True:
                cursor, key_list = server.scan(
                    count=REDIS_SCAN_KEYS_COUNT, cursor=cursor, match=match
                )

                if key_list:
                    server.delete(*key_list)

                if cursor == REDIS_SCAN_CURSOR_INITIAL:
                    break
        except redis.exceptions.RedisError as exception:
            raise LockBackendError(
                'Error purging locks; {}'.format(exception)
            ) from exception

    def _init(self, name, timeout):
        self.name = name

        server = self.__class__.get_redis_connection()

        redis_lock_instance = server.lock(
            name='{}{}'.format(REDIS_LOCK_NAME_PREFIX, name), timeout=timeout
        )

        try:
            result = redis_lock_instance.acquire(blocking=False)
        except redis.exceptions.RedisError as exception:
            raise LockBackendError(
                'Error acquiring lock `{}`; {}'.format(name, exception)
            ) from exception

        if not result:
            raise LockError(
                'Unable to acquire lock `{}`'.format(name)
            )

        self._redis_lock_instance = redis_lock_instance

    def _release(self):
        try:
            self._redis_lock_instance.release()
        except redis.exceptions.LockNotOwnedError:
            """
            The lock expired and was acquired by someone else. It is not
            this instance's lock to release.
            """
        except redis.exceptions.RedisError as exception:
            raise LockBackendError(
                'Error releasing lock `{}`; {}'.format(self.name, exception)
            ) from exception
