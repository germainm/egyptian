from django.apps import apps
from django.db import transaction

from .base import LockingBackend


class ModelLock(LockingBackend):
    @classmethod
    def _acquire_lock(cls, name, timeout):
        Lock = apps.get_model(app_label='lock_manager', model_name='Lock')
        return ModelLock(
            model_instance=Lock.objects.acquire_lock(
                name=name, timeout=timeout
            )
        )

    @classmethod
    def _purge_locks(cls):
        Lock = apps.get_model(app_label='lock_manager', model_name='Lock')

        with transaction.atomic():
            queryset = Lock.objects.select_for_update()

            queryset.delete()

    def _init(self, model_instance):
        self.model_instance = model_instance
        self.name = model_instance.name

    def _release(self):
        self.model_instance.release()
