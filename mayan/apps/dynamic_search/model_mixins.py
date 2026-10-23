import json

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import F

from .search_models import SearchModel
from .settings import setting_saved_resultset_time_to_live_increment


class SavedResultsetBusinessLogicModelMixin:
    def get_content_type(self):
        content_type = ContentType.objects.get_by_natural_key(
            app_label=self.app_label, model=self.model_name
        )

        return content_type

    def get_model_class(self):
        content_type = self.get_content_type()

        return content_type.model_class()

    def get_result_queryset(self):
        SavedResultset = apps.get_model(
            app_label='dynamic_search', model_name='SavedResultset'
        )

        SavedResultset.objects.update(
            time_to_live=F('time_to_live') + setting_saved_resultset_time_to_live_increment.value
        )

        content_type = self.get_content_type()

        values_list = self.entries.values_list('object_id', flat=True)

        queryset = content_type.get_all_objects_for_this_type()
        queryset = queryset.filter(pk__in=values_list)

        return queryset

    def get_search_model(self):
        model_class = self.get_model_class()

        return SearchModel.get_for_model(instance=model_class)

    def get_search_query_dict(self):
        obj = json.loads(s=self.search_query_text)

        return obj
