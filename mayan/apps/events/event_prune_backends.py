from django.db.models import CharField, Value
from django.db.models.expressions import OuterRef, Subquery
from django.db.models.functions import Concat
from django.utils import timezone
from django.utils.module_loading import import_string

from actstream.models import Action

from .settings import (
    setting_event_prune_backend, setting_event_prune_backend_arguments
)


class EventLogPruneBackend:
    @classmethod
    def get_backend_class(cls):
        return import_string(dotted_path=setting_event_prune_backend.value)

    @classmethod
    def get_backend_instance(cls):
        backend_class = cls.get_backend_class()

        return backend_class(**setting_event_prune_backend_arguments.value)

    def _execute(self):
        return NotImplementedError

    def execute(self):
        self._execute()


class EventLogPruneBackendLatest(EventLogPruneBackend):

    def __init__(self, number):
        self.number = number

    def _execute(self):
        queryset_remain = Action.objects.order_by('-timestamp').values_list('pk')[:self.number]
        queryset_delete = Action.objects.exclude(pk__in=queryset_remain)
        queryset_delete.delete()


class EventLogPruneBackendLatestPerObject(EventLogPruneBackend):

    def __init__(self, number):
        self.number = number

    def _execute(self):
        queryset_annotated = Action.objects.values(
            'target_content_type', 'target_object_id', 'verb'
        ).annotate(
            ct_fk_combination=Concat(
                'target_content_type', Value('-'), 'target_object_id',
                output_field=CharField()
            )
        )

        queryset_lastest_per_object = queryset_annotated.filter(
            pk__in=Subquery(
                queryset_annotated.filter(
                    ct_fk_combination=OuterRef('ct_fk_combination')
                ).order_by('-timestamp').values('pk')[:self.number]
            )
        )

        queryset_delete = Action.objects.exclude(
            pk__in=queryset_lastest_per_object.values_list('pk')
        )

        queryset_delete.delete()


class EventLogPruneBackendLatestPerObjectEventType(EventLogPruneBackend):

    def __init__(self, number):
        self.number = number

    def _execute(self):
        queryset_annotated = Action.objects.values(
            'target_content_type', 'target_object_id', 'verb'
        ).annotate(
            ct_fk_verb_combination=Concat(
                'target_content_type', Value('-'), 'target_object_id',
                Value('-'), 'verb', output_field=CharField()
            )
        )

        queryset_lastest_per_object = queryset_annotated.filter(
            pk__in=Subquery(
                queryset_annotated.filter(
                    ct_fk_verb_combination=OuterRef('ct_fk_verb_combination')
                ).order_by('-timestamp').values('pk')[:self.number]
            )
        )

        queryset_delete = Action.objects.exclude(
            pk__in=queryset_lastest_per_object.values_list('pk')
        )

        queryset_delete.delete()


class EventLogPruneBackendOlderThanDays(EventLogPruneBackend):

    def __init__(self, days):
        self.days = days

    def _execute(self):
        cutoff_datetime = timezone.now() - timezone.timedelta(days=self.days)
        queryset = Action.objects.filter(timestamp__lt=cutoff_datetime)
        queryset.delete()
