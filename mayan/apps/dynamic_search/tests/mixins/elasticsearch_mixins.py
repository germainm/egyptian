from unittest import mock

from ...backends.elasticsearch import ElasticsearchSearchBackend

BACKEND_ARGUMENT_LIST = (
    'indices_namespace',
    'search_page_size',
    'point_in_time_keep_alive',
    'refresh_on_search'
)


class ElasticsearchsearchMockBackendMixin:
    def _get_test_backend(self, **kwargs):
        backend = ElasticsearchSearchBackend.__new__(
            ElasticsearchSearchBackend
        )
        backend.client_kwargs = {}

        backend.indices_namespace = 'test'
        backend.refresh_on_search = False
        backend.point_in_time_keep_alive = '1m'
        backend.search_page_size = 10

        for key, value in kwargs.items():
            if key in BACKEND_ARGUMENT_LIST:
                setattr(backend, key, value)

        backend._client = mock.Mock()
        backend._client.open_point_in_time.return_value = {'id': 'pit-id'}

        return backend

    def _do_search_execute(self, backend):
        with mock.patch.object(
            target=ElasticsearchSearchBackend,
            attribute='_get_model_for_index', return_value=mock.Mock()
        ):
            with mock.patch(
                target='mayan.apps.dynamic_search.backends.elasticsearch.backend.Search'
            ):
                search = mock.MagicMock()
                results = backend.do_search_execute(
                    index_name='test-index', search=search
                )
                list(results)
