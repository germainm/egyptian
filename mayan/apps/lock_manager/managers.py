import datetime
import logging

from django.db import OperationalError, models, transaction
from django.db.utils import IntegrityError
from django.utils.timezone import now

from .exceptions import LockBackendError, LockError
from .settings import setting_default_lock_timeout

logger = logging.getLogger(name=__name__)


class LockManager(models.Manager):
    def _do_lock_acquire_stale(self, name, timeout):
        try:
            lock = self.get(name=name)
        except self.model.DoesNotExist:
            logger.debug('lock: %s does not exist', name)
            raise LockError(
                'Unable to acquire lock `{}`'.format(name)
            )

        expiration_datetime = lock.creation_datetime + datetime.timedelta(
            seconds=lock.timeout
        )

        if now() <= expiration_datetime:
            logger.debug('unable to acquire lock: %s', name)
            raise LockError(
                'Unable to acquire lock `{}`'.format(name)
            )

        logger.debug('trying to reacquire stale lock: %s', name)

        creation_datetime = now()

        updated_count = self.filter(
            creation_datetime=lock.creation_datetime, name=name
        ).update(creation_datetime=creation_datetime, timeout=timeout)

        if not updated_count:
            logger.debug('lost the race to reacquire stale lock: %s', name)
            raise LockError(
                'Unable to acquire lock `{}`'.format(name)
            )

        lock.creation_datetime = creation_datetime
        lock.timeout = timeout

        logger.debug('reacquired stale lock: %s', name)

        return lock

    def acquire_lock(self, name, timeout=None):
        logger.debug('trying to acquire lock: %s', name)

        timeout = timeout or setting_default_lock_timeout.value

        lock = self.model(name=name, timeout=timeout)

        try:
            with transaction.atomic():
                lock.save(force_insert=True)
        except IntegrityError as exception:
            logger.debug('IntegrityError: %s', exception)

            return self._do_lock_acquire_stale(name=name, timeout=timeout)
        except OperationalError as exception:
            raise LockBackendError(
                'Operational error while trying to acquire lock: {}; '
                '{}'.format(name, exception)
            ) from exception
        else:
            logger.debug('acquired lock: %s', name)
            return lock
