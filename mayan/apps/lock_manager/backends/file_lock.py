import hashlib
import json
import logging
from pathlib import Path
import threading
import time
import uuid

from django.conf import settings
from django.core.files import locks
from django.utils.encoding import force_bytes

from mayan.apps.storage.settings import setting_temporary_directory

from ..exceptions import LockBackendError, LockError

from .base import LockingBackend

lock = threading.Lock()
logger = logging.getLogger(name=__name__)


class FileLock(LockingBackend):
    @classmethod
    def _acquire_lock(cls, name, timeout):
        instance = FileLock(name=name, timeout=timeout)
        return instance

    @classmethod
    def _initialize(cls):
        string = force_bytes(s=settings.SECRET_KEY)
        hash_object = hashlib.sha256(string=string)
        hexdigest = hash_object.hexdigest()

        cls.path_lock_file = Path(
            setting_temporary_directory.value, hexdigest
        )
        cls.path_lock_file.touch()

        logger.debug('path_lock_file: %s', cls.path_lock_file)

    @classmethod
    def _file_locks_load(cls, file_object):
        file_object.seek(0)

        data = file_object.read()

        if not data:
            return {}

        try:
            return json.loads(s=data)
        except ValueError:
            logger.error(
                'Lock file: %s, is corrupted. Discarding its contents.',
                cls.path_lock_file
            )
            return {}

    @classmethod
    def _file_locks_save(cls, file_locks, file_object):
        file_object.seek(0)
        file_object.truncate()
        string = json.dumps(obj=file_locks)
        file_object.write(string)

    @classmethod
    def _file_object_lock(cls, file_object):
        if not locks.lock(f=file_object, flags=locks.LOCK_EX):
            raise LockBackendError(
                'Unable to lock the lock file: {}. The filesystem does not '
                'support locking. Locking between processes is not '
                'guaranteed.'.format(cls.path_lock_file)
            )

    @classmethod
    def _purge_locks(cls):
        with lock:
            with cls.path_lock_file.open(mode='r+') as file_object:
                cls._file_object_lock(file_object=file_object)
                cls._file_locks_save(file_locks={}, file_object=file_object)

    def _get_lock_dictionary(self):
        if self.timeout:
            result = {
                'expiration': time.time() + self.timeout,
                'uuid': self.uuid
            }
        else:
            result = {
                'expiration': 0,
                'uuid': self.uuid
            }

        return result

    def _init(self, name, timeout):
        self.name = name
        self.timeout = timeout
        self.uuid = str(
            uuid.uuid4()
        )

        cls = self.__class__

        with lock:
            with cls.path_lock_file.open(mode='r+') as file_object:
                cls._file_object_lock(file_object=file_object)

                file_locks = cls._file_locks_load(file_object=file_object)

                now = time.time()

                file_locks = {
                    key: value for key, value in file_locks.items() if not value['expiration'] or now <= value['expiration'] or key == name
                }

                if name in file_locks:
                    if file_locks[name]['expiration'] and now > file_locks[name]['expiration']:
                        file_locks[name] = self._get_lock_dictionary()
                    else:
                        cls._file_locks_save(
                            file_locks=file_locks, file_object=file_object
                        )
                        raise LockError(
                            'Unable to acquire lock `{}`'.format(name)
                        )
                else:
                    file_locks[name] = self._get_lock_dictionary()

                cls._file_locks_save(
                    file_locks=file_locks, file_object=file_object
                )

    def _release(self):
        cls = self.__class__

        with lock:
            with cls.path_lock_file.open(mode='r+') as file_object:
                cls._file_object_lock(file_object=file_object)

                file_locks = cls._file_locks_load(file_object=file_object)

                if self.name in file_locks:
                    if file_locks[self.name]['uuid'] == self.uuid:
                        file_locks.pop(self.name)
                    else:
                        """Lock expired and someone else acquired it."""
                else:
                    """Lock expired and someone else released it."""

                cls._file_locks_save(
                    file_locks=file_locks, file_object=file_object
                )
