import hashlib
from datetime import timedelta

from django.db import models, transaction
from django.utils import timezone
from django.utils.encoding import force_bytes


class TaskDeduplicationEntryManager(models.Manager):
    @staticmethod
    def get_condition_stale(queued_interval, stale_interval):
        datetime_now = timezone.now()

        datetime_queued = datetime_now - timedelta(seconds=queued_interval)
        datetime_stale = datetime_now - timedelta(seconds=stale_interval)

        condition_queued = models.Q(
            datetime_created__lt=datetime_queued, datetime_started__isnull=True
        )
        condition_started = models.Q(datetime_started__lt=datetime_stale)

        return condition_queued | condition_started

    @staticmethod
    def get_key_hash(key):
        string = force_bytes(s=key)

        hash_object = hashlib.sha256(string=string)

        return hash_object.hexdigest()

    def do_entry_create(self, dotted_path, key, queued_interval, stale_interval):
        key_hash = self.get_key_hash(key=key)

        entry, created = self.get_or_create(
            defaults={'key': key}, dotted_path=dotted_path, key_hash=key_hash
        )

        if created:
            return True

        queryset = self.filter(pk=entry.pk)

        condition_stale = self.get_condition_stale(
            queued_interval=queued_interval, stale_interval=stale_interval
        )

        queryset_stale = queryset.filter(condition_stale)

        updated_count = queryset_stale.update(
            datetime_created=timezone.now(), datetime_started=None,
            is_dirty=False
        )

        if updated_count:
            return True

        updated_count = queryset.filter(
            datetime_started__isnull=False
        ).update(is_dirty=True)

        if updated_count:
            return False

        if queryset.exists():
            return False

        return True

    def do_entry_delete(self, dotted_path, key):
        key_hash = self.get_key_hash(key=key)

        queryset = self.filter(dotted_path=dotted_path, key_hash=key_hash)

        queryset.delete()

    def do_entry_start(self, dotted_path, key):
        key_hash = self.get_key_hash(key=key)

        queryset = self.filter(dotted_path=dotted_path, key_hash=key_hash)

        queryset.update(
            datetime_started=timezone.now()
        )

    def do_entry_release(self, dotted_path, key):
        key_hash = self.get_key_hash(key=key)

        with transaction.atomic():
            queryset = self.select_for_update().filter(
                dotted_path=dotted_path, key_hash=key_hash
            )

            entry_list = list(queryset)

            if not entry_list:
                return False

            entry = entry_list[0]

            if entry.is_dirty:
                entry.datetime_created = timezone.now()
                entry.datetime_started = None
                entry.is_dirty = False
                entry.save(
                    update_fields=(
                        'datetime_created', 'datetime_started', 'is_dirty'
                    )
                )

                return True

            entry.delete()

            return False

    def do_stale_delete(self, queued_interval, stale_interval):
        condition_stale = self.get_condition_stale(
            queued_interval=queued_interval, stale_interval=stale_interval
        )

        queryset = self.filter(condition_stale)

        deleted_count, deleted_detail = queryset.delete()

        return deleted_count
