from contextlib import contextmanager
from datetime import timedelta
import logging

from django.apps import apps
from django.core.files.base import ContentFile
from django.db.models import F, Sum
from django.template.defaultfilters import filesizeformat
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import EventManagerMethodAfter
from mayan.apps.lock_manager.backends.base import LockingBackend
from mayan.apps.lock_manager.decorators import (
    acquire_lock_class_method, locked_class_method, release_lock_class_method
)
from mayan.apps.lock_manager.exceptions import LockError
from mayan.apps.storage.classes import DefinedStorage

from .events import event_cache_partition_purged, event_cache_purged
from .exceptions import FileCachingException
from .settings import (
    setting_eviction_grace_period,
    setting_maximum_failed_prune_attempts,
    setting_maximum_normal_prune_attempts
)

logger = logging.getLogger(name=__name__)


class CacheBusinessLogicMixin:
    def get_defined_storage(self):
        try:
            defined_storage_class = DefinedStorage.get(
                name=self.defined_storage_name
            )
        except KeyError:
            defined_storage_class = DefinedStorage(
                dotted_path='', label=_(message='Unknown'), name='unknown'
            )

        return defined_storage_class

    def get_files(self):
        CachePartitionFile = apps.get_model(
            app_label='file_caching', model_name='CachePartitionFile'
        )

        return CachePartitionFile.objects.filter(
            partition__cache__id=self.pk
        )

    def get_maximum_size_display(self):
        return filesizeformat(bytes_=self.maximum_size)

    get_maximum_size_display.help_text = _(
        message='Size at which the cache will start deleting old entries.'
    )
    get_maximum_size_display.short_description = _(message='Maximum size')

    def get_partition_count(self):
        CachePartition = apps.get_model(
            app_label='file_caching', model_name='CachePartition'
        )

        queryset_cache_partitions = CachePartition.objects.filter(cache=self)

        return queryset_cache_partitions.count()

    get_partition_count.short_description = _(message='Partition count')
    get_partition_count.help_text = _(message='Total cached objects.')

    def get_partition_file_count(self):
        queryset_files = self.get_files()
        return queryset_files.count()

    get_partition_file_count.short_description = _(
        message='Partition file count'
    )
    get_partition_file_count.help_text = _(message='Total cached files.')

    def get_queryset_files_for_eviction(self):
        queryset_files = self.get_files()

        queryset_files_sorted = queryset_files.order_by('accessed', 'hits')

        grace_period = setting_eviction_grace_period.value

        if grace_period:
            cutoff_datetime = timezone.now() - timedelta(seconds=grace_period)
            queryset_files_evictable = queryset_files_sorted.filter(
                datetime__lt=cutoff_datetime
            )

            if queryset_files_evictable.exists():
                return queryset_files_evictable

        return queryset_files_sorted

    def get_total_size(self):
        queryset_files = self.get_files()
        queryset_files_aggregated = queryset_files.aggregate(
            file_size__sum=Sum('file_size')
        )

        return queryset_files_aggregated['file_size__sum'] or 0

    def get_total_size_display(self):
        total_size = self.get_total_size()

        size_humanized = filesizeformat(bytes_=total_size)

        size_percent = total_size / self.maximum_size * 100

        return format_lazy(
            '{} ({:0.1f}%)', size_humanized, size_percent
        )

    get_total_size_display.short_description = _(message='Current size')
    get_total_size_display.help_text = _(
        message='Current size of the cache.'
    )

    @cached_property
    def label(self):
        defined_storage_class = self.get_defined_storage()
        return defined_storage_class.label

    label.short_description = _(message='Label')

    def prune(self):
        failed_attempts = 0
        normal_attempts = 0
        file_index = 0

        CachePartitionFile = apps.get_model(
            app_label='file_caching', model_name='CachePartitionFile'
        )

        get_queryset_eviction = self.get_queryset_files_for_eviction()

        while self.get_total_size() >= self.maximum_size:
            try:
                cache_partition_file = get_queryset_eviction[file_index]
            except IndexError:
                file_index = 0
                get_queryset_eviction = self.get_queryset_files_for_eviction()
            else:
                try:
                    cache_partition_file.delete()
                except CachePartitionFile.DoesNotExist:
                    file_index += 1
                except LockError:
                    logger.debug(
                        'Lock error trying to delete file "%s" for '
                        'prune. Skipping and attempting next file.',
                        cache_partition_file
                    )
                    failed_attempts += 1
                    file_index += 1

                    if failed_attempts > setting_maximum_failed_prune_attempts.value:
                        raise FileCachingException(
                            'Too many cache prune attempts failed.'
                        )
                else:
                    file_index = 0
                    normal_attempts += 1

                    if normal_attempts > setting_maximum_normal_prune_attempts.value:
                        raise FileCachingException(
                            'Too many cache prunes trying to create a '
                            'single new file.'
                        )

    @method_event(
        event=event_cache_purged,
        event_manager_class=EventManagerMethodAfter,
        target='self'
    )
    def purge(self, user):
        self._event_actor = user

        try:
            DefinedStorage.get(name=self.defined_storage_name)
        except KeyError:
            """
            Unknown or deleted storage. Must not be purged otherwise only
            the database data will be erased but the actual storage files
            will remain.
            """
        else:
            queryset_partitions = self.partitions.all()

            for partition in queryset_partitions:
                partition._event_action_object = self
                try:
                    partition.purge(user=user)
                except Exception as exception:
                    logger.error(
                        'Unable to purge partition ID: %d; %s',
                        partition.pk, exception
                    )

    @cached_property
    def storage(self):
        defined_storage_class = self.get_defined_storage()
        defined_storage_instance = defined_storage_class.get_storage_instance()

        return defined_storage_instance


class CachePartitionBusinessLogicMixin:
    @staticmethod
    def get_combined_filename(parent, filename):
        return '{}-{}'.format(parent, filename)

    def _lock_manager_get_lock_name(self, filename):
        return self.get_file_lock_name(filename=filename)

    @contextmanager
    def create_file(self, filename):
        self.cache.prune()

        lock_name = self.get_file_lock_name(filename=filename)
        try:
            locking_backend_class = LockingBackend.get_backend()
            lock = locking_backend_class.acquire_lock(name=lock_name)
        except LockError:
            logger.debug('unable to obtain lock: %s', lock_name)
            raise
        else:
            logger.debug('acquired lock: %s', lock_name)

            try:
                try:
                    self.cache.storage.delete(
                        name=self.get_full_filename(filename=filename)
                    )
                except Exception as exception:
                    """
                    Some S3 implementations like Google Cloud Storage throw
                    an error when attempting to delete a not existent file
                    key. Ignore this exception, any storage error of concern
                    will be triggered by the ``storage.save`` call below.
                    """
                    logger.debug(
                        'cache.storage.delete exception: %s', exception
                    )

                self.cache.storage.save(
                    name=self.get_full_filename(filename=filename),
                    content=ContentFile(content=b'')
                )

                partition_file = None

                try:
                    partition_file = self.files.create(filename=filename)
                    yield partition_file._open_for_writing(
                        _acquire_lock=False
                    )
                except Exception as exception:
                    logger.error(
                        'Unexpected exception while trying to save new '
                        'cache file; %s', exception, exc_info=True
                    )
                    if partition_file:
                        partition_file.delete(_acquire_lock=False)
                    else:
                        self.cache.storage.delete(
                            name=self.get_full_filename(filename=filename)
                        )
                    raise
                else:
                    partition_file.close(_acquire_lock=False)
                    partition_file._update_size(_acquire_lock=False)
            finally:
                lock.release()

    def get_file(self, filename):
        return self.files.get(filename=filename)

    def get_file_lock_name(self, filename):
        return 'cache_partition-file-{}-{}-{}'.format(
            self.cache.pk, self.pk, filename
        )

    def get_full_filename(self, filename):
        CachePartition = apps.get_model(
            app_label='file_caching', model_name='CachePartition'
        )

        return CachePartition.get_combined_filename(
            parent=self.name, filename=filename
        )

    def get_total_size(self):
        queryset_files = self.files
        queryset_files_aggregated = queryset_files.aggregate(
            file_size__sum=Sum('file_size')
        )

        return queryset_files_aggregated['file_size__sum'] or 0

    def get_total_size_display(self):
        return filesizeformat(
            bytes_=self.get_total_size()
        )

    get_total_size_display.short_description = _(message='Current size')
    get_total_size_display.help_text = _(
        message='Current size of the cache partition.'
    )

    @method_event(
        event=event_cache_partition_purged,
        event_manager_class=EventManagerMethodAfter,
        target='self'
    )
    def purge(self, user):
        self._event_actor = user
        queryset_files = self.files.all()

        for parition_file in queryset_files:
            try:
                parition_file.delete()
            except Exception as exception:
                logger.error(
                    'Unable to delete partition file ID: %d; %s',
                    parition_file.pk, exception
                )


class CachePartitionFileBusinessLogicMixin:
    def _lock_manager_get_lock_name(self, *args, **kwargs):
        return self.partition.get_file_lock_name(filename=self.filename)

    @acquire_lock_class_method
    def _open_for_writing(self):
        try:
            storage_instance = self.partition.cache.storage

            self._storage_object = storage_instance.open(
                mode='wb', name=self.full_filename
            )
            return self._storage_object
        except Exception as exception:
            logger.error(
                'Unexpected exception opening the cache file; %s', exception,
                exc_info=True
            )
            raise

    @locked_class_method
    def _update_size(self):
        storage_instance = self.partition.cache.storage
        self.file_size = storage_instance.size(name=self.full_filename)
        self.save(
            update_fields=('file_size',)
        )
        if self.file_size > self.partition.cache.maximum_size:
            raise FileCachingException(
                'Cache partition file %s is bigger than the maximum cache '
                'size.'
            )

    @release_lock_class_method
    def close(self):
        if self._storage_object is not None:
            self._storage_object.close()
        self._storage_object = None

    @cached_property
    def full_filename(self):
        CachePartition = apps.get_model(
            app_label='file_caching', model_name='CachePartition'
        )

        return CachePartition.get_combined_filename(
            parent=self.partition.name, filename=self.filename
        )

    @contextmanager
    def open(self):
        CachePartitionFile = apps.get_model(
            app_label='file_caching', model_name='CachePartitionFile'
        )

        lock_name = self._lock_manager_get_lock_name()

        try:
            locking_backend_class = LockingBackend.get_backend()
            self._lock = locking_backend_class.acquire_lock(name=lock_name)
        except LockError:
            logger.debug('unable to obtain lock: %s', lock_name)
            raise
        else:
            logger.debug('acquired lock: %s', lock_name)

            self._storage_object = None

            try:
                try:
                    storage_instance = self.partition.cache.storage
                    self._storage_object = storage_instance.open(
                        mode='rb', name=self.full_filename
                    )
                except Exception as exception:
                    logger.error(
                        'Unexpected exception opening the cache file; %s',
                        exception, exc_info=True
                    )
                    raise
                else:
                    queryset_partition_files = CachePartitionFile.objects.filter(
                        pk=self.pk
                    )
                    queryset_partition_files.update(
                        accessed=timezone.now(), hits=F('hits') + 1
                    )

                    yield self._storage_object
            finally:
                try:
                    self.close(_acquire_lock=False)
                finally:
                    self._lock.release()
