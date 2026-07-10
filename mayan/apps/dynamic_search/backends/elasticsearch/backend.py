from collections import deque
from contextlib import contextmanager
import functools
import threading

import elasticsearch
from elasticsearch import Elasticsearch, helpers
from elasticsearch.dsl import Q, Search

from mayan.literals import DEFAULT_ELASTICSEARCH_PASSWORD

from ...exceptions import (
    DynamicSearchBackendException, DynamicSearchRetry,
    DynamicSearchValueTransformationError
)
from ...search_backends import SearchBackend
from ...search_fields import SearchFieldVirtualAllFields
from ...search_models import SearchModel
from ...settings import setting_results_limit

from .literals import (
    DEFAULT_ELASTICSEARCH_HOSTS, DEFAULT_ELASTICSEARCH_INDICES_NAMESPACE,
    DEFAULT_ELASTICSEARCH_INDICES_NAMESPACE_TEST,
    DEFAULT_ELASTICSEARCH_POINT_IN_TIME_KEEP_ALIVE,
    DEFAULT_ELASTICSEARCH_SEARCH_PAGE_SIZE,
    DJANGO_TO_ELASTICSEARCH_FIELD_MAP, INDEX_NAME_DELIMITER
)


class ElasticsearchSearchBackend(SearchBackend):
    _client_registry = {}
    _client_registry_lock = threading.Lock()

    feature_reindex = True
    field_type_mapping = DJANGO_TO_ELASTICSEARCH_FIELD_MAP

    def __init__(
        self, client_kwargs=None,
        indices_namespace=DEFAULT_ELASTICSEARCH_INDICES_NAMESPACE,
        search_page_size=DEFAULT_ELASTICSEARCH_SEARCH_PAGE_SIZE,
        point_in_time_keep_alive=DEFAULT_ELASTICSEARCH_POINT_IN_TIME_KEEP_ALIVE,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.indices_namespace = indices_namespace
        self.point_in_time_keep_alive = point_in_time_keep_alive
        # Cap the page size to the results limit so ES never allocates a
        # top-N heap larger than the number of results we will actually use.
        self.search_page_size = min(
            search_page_size, setting_results_limit.value
        )

        self.client_kwargs = client_kwargs or {
            'basic_auth': ('elastic', DEFAULT_ELASTICSEARCH_PASSWORD),
            'hosts': DEFAULT_ELASTICSEARCH_HOSTS,
            'verify_certs': False
        }

        if self._test_mode:
            self.indices_namespace = DEFAULT_ELASTICSEARCH_INDICES_NAMESPACE_TEST

    @property
    def _client(self):
        cls = self.__class__
        cache_key = self._get_client_cache_key()
        client = cls._client_registry.get(cache_key)

        if client is None:
            with cls._client_registry_lock:
                client = cls._client_registry.get(cache_key)
                if client is None:
                    client = Elasticsearch(**self.client_kwargs)
                    cls._client_registry[cache_key] = client

        return client

    @_client.setter
    def _client(self, value):
        cls = self.__class__
        cache_key = self._get_client_cache_key()
        cls._client_registry[cache_key] = value

    def _get_client_cache_key(self):
        items = self.client_kwargs.items()
        return repr(
            sorted(items)
        )

        # Shared PIT id active during a top-level search() call.
        # None means no shared PIT is active; each do_search_execute call
        # will open and close its own PIT independently.
        self._active_pit_id = None

    @contextmanager
    def _pit_context(self, index_name):
        """
        Open a Point-in-Time for index_name, expose its id via
        self._active_pit_id for the duration of the block, then close it.

        This context manager is entered once at the top of search() so that
        every do_search_execute() call within the same request reuses the
        same PIT instead of opening and closing one per scope.
        """
        pit = self._client.open_point_in_time(
            index=index_name, keep_alive=self.point_in_time_keep_alive
        )
        self._active_pit_id = pit['id']
        try:
            yield self._active_pit_id
        finally:
            try:
                self._client.close_point_in_time(id=self._active_pit_id)
            except elasticsearch.exceptions.NotFoundError:
                """PIT already expired — safe to ignore."""
            finally:
                self._active_pit_id = None

    def do_search_execute(self, index_name, search):
        """
        Execute a paginated Elasticsearch search using search_after + PIT,
        sorted by relevance score descending.

        Sort strategy:
          primary   — _score descending: most relevant results come first.
                      With SEARCH_QUERY_RESULTS_LIMIT set to a small value
                      (e.g. 200), the user always sees the best matches
                      rather than the oldest documents.
          secondary — _shard_doc ascending: deterministic tiebreak required
                      by ES for correct search_after pagination. Without it,
                      two documents with the same score could swap positions
                      between pages, causing duplicates or gaps.

        If self._active_pit_id is set (i.e. we are inside a _pit_context
        block), the existing PIT is reused and its lifecycle is NOT managed
        here. Otherwise a new PIT is opened and closed within this method.
        """
        model = self._get_model_for_index(index_name=index_name)
        #self._client.indices.refresh(index=index_name)

        pk_field = model._meta.pk

        owned_pit = self._active_pit_id is None
        if owned_pit:
            pit = self._client.open_point_in_time(
                index=index_name, keep_alive=self.point_in_time_keep_alive
            )
            pit_id = pit['id']
        else:
            pit_id = self._active_pit_id

        base = (
            Search(using=self._client)
            .extra(
                pit={
                    'id': pit_id, 'keep_alive': self.point_in_time_keep_alive
                },
                size=self.search_page_size,
                track_total_hits=False
            )
            .sort(
                {'_score': {'order': 'desc'}},
                {'_shard_doc': {'order': 'asc'}}
            )
            .source(False)
        )

        query_dict = search.to_dict().get('query')
        if query_dict:
            base = base.update_from_dict(
                {'query': query_dict}
            )

        search_after = None

        try:
            while True:
                if search_after is None:
                    search_new = base
                else:
                    search_new = search_new.extra(search_after=search_after)

                response = search_new.execute()

                if not response or not len(response):
                    break

                for entry in response:
                    result_id = entry.meta.id
                    yield pk_field.to_python(value=result_id)

                search_after = response[-1].meta.sort
        except elasticsearch.exceptions.NotFoundError as exception:
            raise DynamicSearchBackendException(
                'Index not found. Make sure the search engine '
                'was properly initialized or upgraded if '
                'it already existed.'
            ) from exception
        finally:
            if owned_pit:
                self._client.close_point_in_time(id=pit_id)

    def _get_index_name(self, search_model):
        return '{}{}{}'.format(
            self.indices_namespace, INDEX_NAME_DELIMITER,
            search_model.full_name
        )

    @functools.lru_cache(maxsize=256)
    def _get_model_for_index(self, index_name):
        indices_namespace, search_model_name = index_name.split(
            INDEX_NAME_DELIMITER
        )
        search_model = SearchModel.get(name=search_model_name)
        model = search_model.model

        return model

    @functools.cache
    def _get_search_model_index_mappings(self, search_model):
        mappings = {}

        field_map = self.get_resolved_field_type_map(
            search_model=search_model
        )
        for field_name, search_field_data in field_map.items():
            mappings[field_name] = {
                'type': search_field_data['field'].name
            }

            if 'analyzer' in search_field_data:
                mappings[field_name]['analyzer'] = search_field_data['analyzer']

        return mappings

    def _get_status(self):
        result = []

        title = 'Elasticsearch search model indexing status'
        title_length = len(title)
        result.append(title)
        result.append('=' * title_length)

        for search_model in SearchModel.all():
            index_name = self._get_index_name(search_model=search_model)
            try:
                index_stats = self._client.count(index=index_name)
            except elasticsearch.exceptions.NotFoundError:
                index_stats = {}

            count = index_stats.get('count', 'None')

            result.append(
                '{}: {}'.format(search_model.label, count)
            )

        return '\n'.join(result)

    def _initialize(self):
        self._update_mappings()

    def search(
        self, query, search_model, user, store_resultset=False, queryset=None
    ):
        """
        Override the base search() to open a single shared PIT for the
        entire request before delegating to the parent implementation.

        All do_search_execute() calls triggered while resolving scopes will
        detect self._active_pit_id and reuse the same PIT instead of each
        opening and closing their own.
        """
        index_name = self._get_index_name(search_model=search_model)
        with self._pit_context(index_name=index_name):
            return super().search(
                query=query, search_model=search_model, user=user,
                store_resultset=store_resultset, queryset=queryset
            )

    def _search_all_fields(
        self, search_field, query_type, value, is_quoted_value=False,
        is_raw_value=False
    ):
        """
        Optimized path for SearchFieldVirtualAllFields.

        Instead of executing one Elasticsearch query per concrete field
        (N round-trips, N PIT open/close cycles), this method builds a
        single bool/should query that covers all compatible fields and
        executes it in one request.

        Fields whose value cannot be transformed for the given query type
        (DynamicSearchValueTransformationError) are silently skipped,
        matching the behaviour of the original sequential loop.
        """
        index_name = self._get_index_name(
            search_model=search_field.search_model
        )

        should_clauses = []

        for concrete_field in search_field.field_composition:
            try:
                field_query = query_type.resolve_for_backend(
                    is_quoted_value=is_quoted_value,
                    is_raw_value=is_raw_value,
                    search_backend=self,
                    search_field=concrete_field,
                    value=value
                )
            except DynamicSearchValueTransformationError:
                # This field type is incompatible with the value; skip it.
                continue

            if field_query is not None:
                should_clauses.append(field_query)

        if not should_clauses:
            return

        combined_query = Q('bool', should=should_clauses, minimum_should_match=1)
        search = Search(index=index_name, using=self._client).filter(combined_query)

        yield from self.do_search_execute(index_name=index_name, search=search)

    def _search(
        self, search_field, query_type, value, is_quoted_value=False,
        is_raw_value=False
    ):
        self.do_query_type_verify(
            query_type=query_type, search_field=search_field
        )

        index_name = self._get_index_name(
            search_model=search_field.search_model
        )

        if isinstance(search_field, SearchFieldVirtualAllFields):
            yield from self._search_all_fields(
                search_field=search_field,
                query_type=query_type,
                value=value,
                is_quoted_value=is_quoted_value,
                is_raw_value=is_raw_value
            )
        else:
            search = Search(index=index_name, using=self._client)

            try:
                search_field_query = query_type.resolve_for_backend(
                    is_quoted_value=is_quoted_value,
                    is_raw_value=is_raw_value, search_backend=self,
                    search_field=search_field, value=value
                )
            except DynamicSearchValueTransformationError:
                return
            else:
                if search_field_query is None:
                    return
                else:
                    search = search.filter(search_field_query)

                    yield from self.do_search_execute(
                        index_name=index_name, search=search
                    )

    def _update_mappings(self, search_model=None):
        if search_model:
            search_models = (search_model,)
        else:
            search_models = SearchModel.all()

        for search_model in search_models:
            index_name = self._get_index_name(search_model=search_model)

            try:
                self._client.indices.delete(index=index_name)
            except elasticsearch.exceptions.NotFoundError:
                """
                Non fatal, might be that this is the first time
                the method is executed. Proceed.
                """

            mappings = self._get_search_model_index_mappings(
                search_model=search_model
            )

            try:
                self._client.indices.create(
                    index=index_name,
                    mappings={'properties': mappings}
                )
            except elasticsearch.exceptions.RequestError:
                try:
                    self._client.indices.put_mapping(
                        index=index_name, properties=mappings
                    )
                except elasticsearch.exceptions.RequestError:
                    """
                    There are mapping changes that were not allowed.
                    Example: Text to Keyword.
                    Boot up regardless and allow user to reindex to delete
                    old indices.
                    """

    def deindex_instance(self, instance):
        search_model = SearchModel.get_for_model(instance=instance)
        index_name = self._get_index_name(search_model=search_model)
        try:
            self._client.delete(id=instance.pk, index=index_name)
        except elasticsearch.exceptions.NotFoundError:
            """
            The document is not present in the index. This happens when the
            instance was never indexed or was already deindexed.
            """

    def index_instance(
        self, instance, exclude_model=None, exclude_kwargs=None
    ):
        search_model = SearchModel.get_for_model(instance=instance)

        document = search_model.populate(
            exclude_kwargs=exclude_kwargs, exclude_model=exclude_model,
            instance=instance, search_backend=self
        )
        index_name = self._get_index_name(search_model=search_model)
        try:
            self._client.index(
                document=document, id=instance.pk, index=index_name
            )
        except (
            elasticsearch.exceptions.ConnectionError,
            elasticsearch.exceptions.ConnectionTimeout
        ) as exception:
            # Transient transport errors are retried instead of being
            # allowed to propagate as a permanent failure that would leave
            # the instance missing from the search index.
            raise DynamicSearchRetry from exception

    def index_instances(self, search_model, id_list):
        index_name = self._get_index_name(search_model=search_model)

        def generate_actions():
            queryset = search_model.get_queryset()
            queryset = queryset.filter(pk__in=id_list)

            for instance in queryset:
                kwargs = search_model.populate(
                    search_backend=self, instance=instance
                )
                kwargs['_id'] = kwargs['id']

                yield kwargs

        action = generate_actions()
        bulk_indexing_generator = helpers.streaming_bulk(
            actions=action, client=self._client, index=index_name,
            yield_ok=False
        )

        try:
            deque(iterable=bulk_indexing_generator, maxlen=0)
        except (
            elasticsearch.exceptions.ConnectionError,
            elasticsearch.exceptions.ConnectionTimeout
        ) as exception:
            # Transient transport errors are retried instead of being
            # allowed to propagate as a permanent failure that would leave
            # instances missing from the search index.
            raise DynamicSearchRetry from exception

    def refresh(self):
        for search_model in SearchModel.all():
            index_name = self._get_index_name(search_model=search_model)

            try:
                self._client.indices.refresh(index=index_name)
            except elasticsearch.exceptions.NotFoundError:
                """Ignore non existent indexes."""

    def reset(self, search_model=None):
        self.tear_down(search_model=search_model)
        self._update_mappings(search_model=search_model)

    def tear_down(self, search_model=None):
        if search_model:
            search_models = (search_model,)
        else:
            search_models = SearchModel.all()

        for search_model in search_models:
            index_name = self._get_index_name(search_model=search_model)
            try:
                self._client.indices.delete(index=index_name)
            except elasticsearch.exceptions.NotFoundError:
                """Ignore non existent indexes."""
