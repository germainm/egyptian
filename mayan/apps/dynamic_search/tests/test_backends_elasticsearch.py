from unittest import mock

import elasticsearch

from mayan.apps.testing.tests.base import BaseTestCase

from ..backends.elasticsearch import ElasticsearchSearchBackend
from ..exceptions import DynamicSearchBackendException, DynamicSearchRetry
from ..search_models import SearchModel
from ..search_query_types import QueryTypeExact

from .mixins.backend_mixins import (
    BackendSearchTestMixin, ElasticsearchSearchBackendTestMixin,
    SearchBackendLimitTestMixin
)
from .mixins.backend_query_type_mixins import (
    BackendFieldTypeQueryTypeTestCaseMixin
)
from .mixins.backend_search_field_mixins import (
    BackendSearchFieldTestCaseMixin
)
from .mixins.base import TestSearchObjectSimpleTestMixin


class ElasticsearchSearchBackendRetryTestCase(BaseTestCase):
    def _get_test_backend(self):
        backend = ElasticsearchSearchBackend.__new__(
            ElasticsearchSearchBackend
        )
        backend.client_kwargs = {}
        backend.indices_namespace = 'test'
        backend._client = mock.Mock()

        return backend

    def test_index_instance_connection_error_is_retried(self):
        backend = self._get_test_backend()
        backend._client.index.side_effect = elasticsearch.exceptions.ConnectionError(
            'Simulated connection error.'
        )

        search_model = mock.Mock()
        search_model.full_name = 'app.model'
        search_model.populate.return_value = {}

        instance = mock.Mock()
        instance.pk = 1

        with mock.patch.object(
            target=SearchModel, attribute='get_for_model',
            return_value=search_model
        ):
            with self.assertRaises(expected_exception=DynamicSearchRetry):
                backend.index_instance(instance=instance)

    def test_index_instances_connection_error_is_retried(self):
        backend = self._get_test_backend()

        search_model = mock.Mock()
        search_model.full_name = 'app.model'

        def raising_streaming_bulk(*args, **kwargs):
            raise elasticsearch.exceptions.ConnectionTimeout(
                'Simulated connection timeout.'
            )
            yield  # pragma: no cover

        with mock.patch(
            target='elasticsearch.helpers.streaming_bulk',
            side_effect=raising_streaming_bulk
        ):
            with self.assertRaises(expected_exception=DynamicSearchRetry):
                backend.index_instances(
                    search_model=search_model, id_list=(1,)
                )


class ElasticsearchSearchBackendRefreshTestCase(
    ElasticsearchsearchMockBackendMixin, BaseTestCase
):
    def test_do_search_execute_refresh_enabled(self):
        backend = self._get_test_backend(refresh_on_search=True)

        self._do_search_execute(backend=backend)
        backend._client.indices.refresh.assert_called_once_with(
            index='test-index'
        )

    def test_do_search_execute_refresh_disabled(self):
        backend = self._get_test_backend(refresh_on_search=False)

        self._do_search_execute(backend=backend)
        backend._client.indices.refresh.assert_not_called()


class ElasticsearchSearchBackendRefreshMissingIndexTestCase(
    ElasticsearchsearchMockBackendMixin, BaseTestCase
):
    def test_refresh_skips_missing_index(self):
        backend = self._get_test_backend()

        search_models = [
            mock.Mock(full_name='app.first'),
            mock.Mock(full_name='app.second'),
            mock.Mock(full_name='app.third')
        ]

        def refresh_side_effect(index):
            if index.endswith('app.second'):
                raise elasticsearch.exceptions.NotFoundError(
                    'Simulated missing index.', meta=None, body=None
                )

        backend._client.indices.refresh.side_effect = refresh_side_effect

        with mock.patch.object(
            target=SearchModel, attribute='all', return_value=search_models
        ):
            backend.refresh()

        self.assertEqual(
            backend._client.indices.refresh.call_count, 3
        )


class ElasticsearchSearchSearchBackendLimitTestCase(
    ElasticsearchSearchBackendTestMixin, SearchBackendLimitTestMixin,
    BaseTestCase
):
    """
    Search limit test case for the Elasticsearch backend.
    """


class ElasticsearchSearchBackendIndexingTestCase(
    BackendSearchTestMixin, ElasticsearchSearchBackendTestMixin,
    TestSearchObjectSimpleTestMixin, BaseTestCase
):
    def test_search_without_indexes(self):
        self._test_search_backend.tear_down()

        with self.assertRaises(expected_exception=DynamicSearchBackendException):
            self._do_backend_search(
                field_name='char',
                query_type=QueryTypeExact,
                value=self._test_object.char
            )


class ElasticsearchSearchBackendSearchFieldTestCase(
    BackendSearchFieldTestCaseMixin, ElasticsearchSearchBackendTestMixin,
    BaseTestCase
):
    """
    Field test case for the Elasticsearch backend.
    """


class ElasticsearchSearchBackendFieldTypeQueryTypeTestCase(
    BackendFieldTypeQueryTypeTestCaseMixin,
    ElasticsearchSearchBackendTestMixin, BaseTestCase
):
    """
    Field query type test case for the Elasticsearch backend.
    """
