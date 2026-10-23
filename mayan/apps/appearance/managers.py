from django.db import models


class UserSettingManager(models.Manager):
    def do_value_get(self, user, namespace, key, default=None):
        try:
            instance = self.get(key=key, namespace=namespace, user=user)
        except self.model.DoesNotExist:
            return default
        else:
            return instance.value

    def do_value_set(self, user, namespace, key, value, _event_actor=None):
        try:
            instance = self.get(key=key, namespace=namespace, user=user)
        except self.model.DoesNotExist:
            instance = self.model(key=key, namespace=namespace, user=user)

        instance._event_actor = _event_actor
        instance.value = value
        instance.save()

        return instance
