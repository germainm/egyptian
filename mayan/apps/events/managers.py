import functools

from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction


class EventSubscriptionManager(models.Manager):
    def create_for(self, stored_event_type, user):
        return self.create(
            stored_event_type=stored_event_type, user=user
        )

    def get_for(self, stored_event_type, user):
        return self.filter(
            stored_event_type=stored_event_type, user=user
        )


class NotificationManager(models.Manager):
    def get_unread(self):
        return self.filter(read=False)


class StoredEventTypeManager(models.Manager):
    _pk_map = {}

    def _do_pk_cache_set(self, name, pk):
        self.__class__._pk_map[name] = pk

    def do_pk_cache_clear(self):
        self.__class__._pk_map = {}

    def get_pk_for_name(self, name):
        pk = self.__class__._pk_map.get(name)

        if pk is not None:
            return pk

        queryset = self.filter(name=name)
        pk_list = list(
            queryset.values_list('pk', flat=True)
        )

        if not pk_list:
            return None

        pk = pk_list[0]

        function_pk_cache_set = functools.partial(
            self._do_pk_cache_set, name=name, pk=pk
        )
        transaction.on_commit(func=function_pk_cache_set, using=self.db)

        return pk


class ObjectEventSubscriptionManager(models.Manager):
    def create_for(self, obj, stored_event_type, user):
        content_type = ContentType.objects.get_for_model(model=obj)

        return self.create(
            content_type=content_type, object_id=obj.pk,
            stored_event_type=stored_event_type, user=user
        )

    def get_for(self, obj, stored_event_type, user):
        content_type = ContentType.objects.get_for_model(model=obj)

        return self.filter(
            content_type=content_type, object_id=obj.pk,
            stored_event_type=stored_event_type, user=user
        )
