from django.apps import apps


class LockBusinessLogicMixin:
    def release(self):
        Lock = apps.get_model(app_label='lock_manager', model_name='Lock')

        try:
            lock = Lock.objects.get(
                name=self.name, creation_datetime=self.creation_datetime
            )
        except Lock.DoesNotExist:
            """
            Our lock has expired and was reassigned.
            """
        else:
            lock.delete()
