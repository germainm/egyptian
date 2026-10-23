import json

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import F, Value
from django.utils.timezone import now

from mayan.apps.databases.manager_mixins import ManagerMinixCreateBulk

from .settings import (
    setting_saved_resultset_results_limit,
    setting_saved_resultset_time_to_live,
    setting_saved_resultsets_per_user_limit
)


class SavedResultsetEntryManager(ManagerMinixCreateBulk, models.Manager):
    pass


class SavedResultsetManager(models.Manager):
    def expired_delete(self):
        datetime_current = now()
        epoch_end = int(
            datetime_current.timestamp()
        )

        queryset = self.annotate(
            epoch_diff=Value(epoch_end) - F('epoch')
        )

        queryset = queryset.filter(
            epoch_diff__gt=F('time_to_live')
        )

        queryset.delete()

    def queryset_save(
        self, queryset, search_explainer_text, search_query, user
    ):
        SavedResultsetEntry = apps.get_model(
            app_label='dynamic_search', model_name='SavedResultsetEntry'
        )

        queryset_per_user = self.filter(user=user).only('id')

        queryset_per_user_to_delete = queryset_per_user[
            setting_saved_resultsets_per_user_limit.value:
        ]

        self.filter(pk__in=queryset_per_user_to_delete).delete()

        content_type = ContentType.objects.get_for_model(model=queryset.model)

        queryset_results = queryset.values_list('pk', flat=True)[
            :setting_saved_resultset_results_limit.value
        ]

        search_query_text = json.dumps(obj=search_query)
        datetime_current = now()
        saved_resultset = self.model(
            app_label=content_type.app_label,
            epoch=datetime_current.timestamp(), model_name=content_type.model,
            result_count=queryset_results.count(),
            search_explainer_text=search_explainer_text,
            search_query_text=search_query_text,
            time_to_live=setting_saved_resultset_time_to_live.value,
            timestamp=datetime_current, user=user
        )
        saved_resultset._event_actor = user
        saved_resultset.save()

        coroutine = SavedResultsetEntry.objects.create_bulk()
        next(coroutine)

        for pk in queryset_results.iterator():
            coroutine.send(
                {'object_id': pk, 'saved_resultset_id': saved_resultset.pk}
            )
        coroutine.close()

        return saved_resultset
