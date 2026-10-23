import logging

from django.apps import apps
from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.utils.module_loading import import_string

from mayan.apps.common.utils import (
    ResolverPipelineModelAttribute, flatten_list, get_class_full_name
)
from .exceptions import DynamicSearchModelException, DynamicSearchQueryError
from .literals import (
    MESSAGE_FEATURE_NO_STATUS, MESSAGE_STATUS_COLUMN_OBJECT_COUNT,
    MESSAGE_STATUS_COLUMN_SEARCH_MODEL, MESSAGE_STATUS_COUNT_UNAVAILABLE,
    MESSAGE_STATUS_TITLE_TEMPLATE
)
from .search_interpreters import SearchInterpreter
from .search_models import SearchModel
from .settings import (
    setting_backend, setting_backend_arguments, setting_results_limit
)

logger = logging.getLogger(name=__name__)


class SearchBackend:
    _initialized = False
    _resolved_field_type_map_cache = {}
    feature_reindex = False
    field_type_mapping = None
    label = None

    @staticmethod
    def _disable():
        for search_model in SearchModel.all():
            post_save.disconnect(
                dispatch_uid='search_handler_index_instance',
                sender=search_model.model
            )
            pre_delete.disconnect(
                dispatch_uid='search_handler_deindex_instance',
                sender=search_model.model
            )

            for proxy in search_model.proxies:
                post_save.disconnect(
                    dispatch_uid='search_handler_index_instance',
                    sender=proxy
                )
                pre_delete.disconnect(
                    dispatch_uid='search_handler_deindex_instance',
                    sender=proxy
                )

            for related_model, path in search_model.get_related_models():
                search_model_full_class_name = get_class_full_name(klass=search_model.model)
                related_model_full_class_name = get_class_full_name(klass=related_model)

                dispatch_uid = 'search_handler_index_related_instance_{}_{}'.format(
                    search_model_full_class_name,
                    related_model_full_class_name
                )
                post_save.disconnect(
                    dispatch_uid=dispatch_uid, sender=related_model
                )

                dispatch_uid = 'search_handler_index_related_instance_delete_{}_{}'.format(
                    search_model_full_class_name,
                    related_model_full_class_name
                )
                pre_delete.disconnect(
                    dispatch_uid=dispatch_uid, sender=related_model
                )

        for through_model, data in SearchModel.get_through_models().items():
            class_full_name = get_class_full_name(klass=through_model)
            dispatch_uid = 'search_handler_index_related_instance_m2m_{}'.format(
                class_full_name
            )
            m2m_changed.disconnect(
                dispatch_uid=dispatch_uid, sender=through_model
            )

    @staticmethod
    def _enable():
        from .handlers import (
            handler_deindex_instance, handler_factory_index_instance,
            handler_factory_index_related_instance_delete,
            handler_factory_index_related_instance_m2m,
            handler_factory_index_related_instance_save
        )

        for search_model in SearchModel.all():
            own_save_field_name_set = search_model.get_own_save_field_name_set()

            receiver_index_instance = handler_factory_index_instance(
                field_name_set=own_save_field_name_set
            )

            post_save.connect(
                dispatch_uid='search_handler_index_instance',
                receiver=receiver_index_instance,
                sender=search_model.model, weak=False
            )
            pre_delete.connect(
                dispatch_uid='search_handler_deindex_instance',
                receiver=handler_deindex_instance,
                sender=search_model.model, weak=False
            )

            for proxy in search_model.proxies:
                post_save.connect(
                    dispatch_uid='search_handler_index_instance',
                    receiver=receiver_index_instance, sender=proxy,
                    weak=False
                )
                pre_delete.connect(
                    dispatch_uid='search_handler_deindex_instance',
                    receiver=handler_deindex_instance,
                    sender=proxy, weak=False
                )

            related_model_save_field_name_map = search_model.get_related_model_save_field_name_map()

            for related_model, path in search_model.get_related_models():
                search_model_full_class_name = get_class_full_name(klass=search_model.model)
                related_model_full_class_name = get_class_full_name(klass=related_model)

                dispatch_uid = 'search_handler_index_related_instance_{}_{}'.format(
                    search_model_full_class_name,
                    related_model_full_class_name
                )
                field_name_set = related_model_save_field_name_map.get(
                    related_model
                )
                receiver = handler_factory_index_related_instance_save(
                    field_name_set=field_name_set, reverse_field_path=path
                )
                post_save.connect(
                    dispatch_uid=dispatch_uid, receiver=receiver,
                    sender=related_model, weak=False
                )

                dispatch_uid = 'search_handler_index_related_instance_delete_{}_{}'.format(
                    search_model_full_class_name,
                    related_model_full_class_name
                )
                receiver = handler_factory_index_related_instance_delete(
                    reverse_field_path=path
                )
                pre_delete.connect(
                    dispatch_uid=dispatch_uid, receiver=receiver,
                    sender=related_model, weak=False
                )

        through_models = SearchModel.get_through_models()

        for through_model, data in through_models.items():
            class_full_name = get_class_full_name(klass=through_model)
            dispatch_uid = 'search_handler_index_related_instance_m2m_{}'.format(
                class_full_name
            )
            receiver = handler_factory_index_related_instance_m2m(
                data=data
            )

            m2m_changed.connect(
                dispatch_uid=dispatch_uid, receiver=receiver,
                sender=through_model, weak=False
            )

    @staticmethod
    def get_class():
        return import_string(dotted_path=setting_backend.value)

    @staticmethod
    def get_instance(extra_kwargs=None):
        kwargs = setting_backend_arguments.value.copy()
        if extra_kwargs:
            kwargs.update(extra_kwargs)

        klass = SearchBackend.get_class()
        return klass(**kwargs)

    @staticmethod
    def limit_queryset(queryset):
        pk_list = queryset.values('pk')[:setting_results_limit.value]
        return queryset.filter(pk__in=pk_list)

    @staticmethod
    def index_related_instance_m2m(
        action, instance, model, pk_set, search_model_related_paths
    ):
        from .tasks import task_index_instance

        if action in ('post_add', 'pre_remove'):
            instance_paths = search_model_related_paths.get(
                instance._meta.model, ()
            )
            model_paths = search_model_related_paths.get(
                model, ()
            )

            if action == 'pre_remove':
                exclude_kwargs = {
                    'exclude_app_label': instance._meta.app_label,
                    'exclude_model_name': instance._meta.model_name,
                    'exclude_kwargs': {'id': instance.pk}
                }
            else:
                exclude_kwargs = {}

            for instance_path in instance_paths:
                result = ResolverPipelineModelAttribute.resolve(
                    attribute=instance_path, obj=instance
                )

                """
                `pk_set` holds primary keys of `model`, so restricting by
                it is only meaningful when the path resolved to objects of
                `model`. A manager and a queryset both carry the model
                they return; anything else, a single instance or a list,
                carries nothing and is left alone.
                """
                if getattr(result, 'model', None) is model:
                    result = result.filter(pk__in=pk_set)

                entries = flatten_list(value=result)

                for entry in entries:
                    task_kwargs = {
                        'app_label': entry._meta.app_label,
                        'model_name': entry._meta.model_name,
                        'object_id': entry.pk
                    }
                    task_kwargs.update(exclude_kwargs)

                    task_index_instance.apply_async(
                        kwargs=task_kwargs
                    )

            if action == 'pre_remove':
                exclude_kwargs = {
                    'exclude_app_label': model._meta.app_label,
                    'exclude_model_name': model._meta.model_name,
                    'exclude_kwargs': {'id__in': pk_set}
                }
            else:
                exclude_kwargs = {}

            for model_instance in model._meta.default_manager.filter(pk__in=pk_set):
                for instance_path in model_paths:
                    result = ResolverPipelineModelAttribute.resolve(
                        attribute=instance_path, obj=model_instance
                    )

                    entries = flatten_list(value=result)

                    for entry in entries:
                        task_kwargs = {
                            'app_label': entry._meta.app_label,
                            'model_name': entry._meta.model_name,
                            'object_id': entry.pk
                        }
                        task_kwargs.update(exclude_kwargs)

                        task_index_instance.apply_async(
                            kwargs=task_kwargs
                        )

    def __init__(self, _test_mode=False):
        self._test_mode = _test_mode

    def _search(
        self, search_field, query_type, value, is_quoted_value=False,
        is_raw_value=False
    ):
        raise NotImplementedError

    def deindex_instance(self, instance):
        pass

    def do_native_type_conversion(self, value):
        return value

    def do_query_type_verify(self, query_type, search_field):
        query_type_set = search_field.get_backend_field_query_type_set(
            search_backend=self
        )
        if query_type not in query_type_set:
            raise DynamicSearchQueryError(
                'The backend `{search_backend}` does not support queries '
                'of type `{query_type}` for the field named '
                '`{search_field}`.'.format(
                    query_type=query_type, search_backend=self,
                    search_field=search_field.field_name
                )
            )

    def get_field_type_mapping(self):
        return self.field_type_mapping or {}

    def get_resolved_field_type_map(self, search_model):
        cache = SearchBackend._resolved_field_type_map_cache
        cache_key = (self.__class__, search_model)

        try:
            return cache[cache_key]
        except KeyError:
            result = {}

            field_type_mapping = self.get_field_type_mapping()

            for search_field in search_model.search_fields:
                try:
                    backend_field_type_dictionary = field_type_mapping[
                        search_field.field_class
                    ]
                except KeyError:
                    raise DynamicSearchModelException(
                        'Unknown field type `{}` for model `{}`'.format(
                            search_field.field_name, search_model.full_name
                        )
                    )
                else:
                    result[
                        search_field.field_name
                    ] = backend_field_type_dictionary

            cache[cache_key] = result

            return result

    def get_search_field_backend_field_type(self, search_field):
        return self.get_resolved_field_type_map(
            search_model=search_field.search_model
        )[search_field.field_name]['field']

    def get_status(self):
        if not hasattr(self, '_get_status'):
            return MESSAGE_FEATURE_NO_STATUS

        status_entry_list = self._get_status()

        backend_label = self.label or self.__class__.__name__

        title = MESSAGE_STATUS_TITLE_TEMPLATE % {'label': backend_label}

        heading_search_model = str(MESSAGE_STATUS_COLUMN_SEARCH_MODEL)
        heading_object_count = str(MESSAGE_STATUS_COLUMN_OBJECT_COUNT)

        row_list = []
        for status_entry in status_entry_list:
            search_model = status_entry['search_model']
            object_count = status_entry['object_count']

            if object_count is None:
                object_count_text = str(MESSAGE_STATUS_COUNT_UNAVAILABLE)
            else:
                object_count_text = str(object_count)

            search_model_text = str(search_model.label)

            row_list.append(
                (search_model_text, object_count_text)
            )

        search_model_text_list = [row[0] for row in row_list]
        search_model_text_list.append(heading_search_model)
        search_model_column_width = max(
            len(text) for text in search_model_text_list
        )

        object_count_text_list = [row[1] for row in row_list]
        object_count_text_list.append(heading_object_count)
        object_count_column_width = max(
            len(text) for text in object_count_text_list
        )

        line_list = []

        line_list.append(title)
        line_list.append(
            '=' * len(title)
        )
        line_list.append('')

        header_line = '{}  {}'.format(
            heading_search_model.ljust(search_model_column_width),
            heading_object_count.rjust(object_count_column_width)
        )
        line_list.append(header_line)

        separator_line = '{}  {}'.format(
            '-' * search_model_column_width,
            '-' * object_count_column_width
        )
        line_list.append(separator_line)

        for search_model_text, object_count_text in row_list:
            data_line = '{}  {}'.format(
                search_model_text.ljust(search_model_column_width),
                object_count_text.rjust(object_count_column_width)
            )
            line_list.append(data_line)

        return '\n'.join(line_list)

    def index_instance(self, instance, exclude_model=None, exclude_kwargs=None):
        pass

    def index_instances(self, search_model, id_list=None):
        pass

    def initialize(self):
        self._initialize()

    def _initialize(self):
        pass

    def refresh(self):
        pass

    def reset(self, search_model=None):
        pass

    def search(
        self, query, search_model, user, store_resultset=False, queryset=None
    ):
        AccessControlList = apps.get_model(
            app_label='acls', model_name='AccessControlList'
        )
        SavedResultset = apps.get_model(
            app_label='dynamic_search', model_name='SavedResultset'
        )

        search_interpreter = SearchInterpreter.init(
            query=query, search_model=search_model
        )

        id_list = search_interpreter.do_resolve(search_backend=self)

        if queryset is None:
            queryset = search_model.get_queryset()

        queryset = queryset.filter(pk__in=id_list)

        if search_model.permission:
            queryset = AccessControlList.objects.restrict_queryset(
                permission=search_model.permission, queryset=queryset,
                user=user
            )

        queryset = SearchBackend.limit_queryset(queryset=queryset)

        if store_resultset:
            search_explainer_text = search_interpreter.to_explain()

            saved_resultset = SavedResultset.objects.queryset_save(
                queryset=queryset,
                search_explainer_text=search_explainer_text,
                search_query=query, user=user
            )
        else:
            saved_resultset = None

        return (saved_resultset, queryset)

    def tear_down(self):
        pass

    def test_mode_stop(self):
        pass

    def upgrade(self):
        pass
