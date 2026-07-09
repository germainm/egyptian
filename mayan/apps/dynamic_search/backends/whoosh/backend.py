import functools
import logging
from pathlib import Path

import whoosh
from whoosh import qparser
from whoosh.filedb.filestore import FileStorage
from whoosh.index import EmptyIndexError
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh.query import Every
from whoosh.writing import BufferedWriter

from django.conf import settings

from mayan.apps.common.utils import any_to_bool
from mayan.apps.lock_manager.backends.base import LockingBackend
from mayan.apps.lock_manager.exceptions import LockError
from mayan.apps.storage.utils import TemporaryDirectory

from ...exceptions import (
    DynamicSearchBackendException, DynamicSearchRetry,
    DynamicSearchValueTransformationError
)
from ...search_backends import SearchBackend
from ...search_fields import SearchFieldVirtualAllFields
from ...search_models import SearchModel

from .literals import (
    DJANGO_TO_WHOOSH_FIELD_MAP, TEXT_LOCK_INSTANCE_DEINDEX,
    TEXT_LOCK_INSTANCE_INDEX, WHOOSH_INDEX_DIRECTORY_NAME
)

logger = logging.getLogger(name=__name__)


class WhooshSearchBackend(SearchBackend):
    _local_attribute_backend_temporary_directory = None
    feature_reindex = True
    field_type_mapping = DJANGO_TO_WHOOSH_FIELD_MAP

    def __init__(
        self, index_path=None, writer_limitmb=128, writer_multisegment=False,
        writer_procs=1, **kwargs
    ):
        super().__init__(**kwargs)

        if self._test_mode:
            if not self.__class__._local_attribute_backend_temporary_directory:
                self.__class__._local_attribute_backend_temporary_directory = TemporaryDirectory()
            index_path = self._local_attribute_backend_temporary_directory.name

        self.index_path = Path(
            index_path or Path(
                settings.MEDIA_ROOT, WHOOSH_INDEX_DIRECTORY_NAME
            )
        )

        if writer_limitmb:
            writer_limitmb = int(writer_limitmb)

        if writer_multisegment:
            writer_multisegment = any_to_bool(value=writer_multisegment)

        if writer_procs:
            writer_procs = int(writer_procs)

        self.writer_kwargs = {
            'limitmb': writer_limitmb, 'multisegment': writer_multisegment,
            'procs': writer_procs
        }

    def _clear_search_model_index(self, search_model):
        schema = self._get_search_model_schema(search_model=search_model)

        if not settings.COMMON_DISABLE_LOCAL_STORAGE:
            # Clear the model index.
            self._get_storage().create_index(
                indexname=search_model.full_name, schema=schema
            )

    def _do_query_resolve(self, index, query):
        with index.searcher() as searcher:
            results = searcher.search(limit=None, q=query)
            for result in results:
                yield int(
                    result['id']
                )

    def _get_or_create_index(self, search_model):
        storage = self._get_storage()
        schema = self._get_search_model_schema(search_model=search_model)

        try:
            # Explicitly specify the schema. Allows using existing index
            # when the schema changes.
            index = storage.open_index(
                indexname=search_model.full_name, schema=schema
            )
        except EmptyIndexError:
            index = storage.create_index(
                indexname=search_model.full_name, schema=schema
            )

        return index

    @functools.cache
    def _get_search_model_schema(self, search_model):
        field_map = self.get_resolved_field_type_map(
            search_model=search_model
        )
        schema_kwargs = {
            key: value['field'] for key, value in field_map.items()
        }

        return whoosh.fields.Schema(**schema_kwargs)

    def _get_status(self):
        result = []

        title = 'Whoosh search model indexing status'
        result.append(title)
        result.append(
            len(title) * '='
        )

        for search_model in SearchModel.all():
            index = self._get_or_create_index(search_model=search_model)

            with index.searcher() as searcher:
                search_results = searcher.search(
                    q=Every('id')
                )

                result.append(
                    '{}: {}'.format(
                        search_model.label, search_results.estimated_length()
                    )
                )

        return '\n'.join(result)

    def _get_storage(self):
        return FileStorage(path=self.index_path)

    def _get_writer(self, search_model):
        index = self._get_or_create_index(search_model=search_model)

        return index.writer(**self.writer_kwargs)

    def _initialize(self):
        if not settings.COMMON_DISABLE_LOCAL_STORAGE:
            self.index_path.mkdir(exist_ok=True)

    def _search(
        self, search_field, query_type, value, is_quoted_value=False,
        is_raw_value=False
    ):
        self.do_query_type_verify(
            query_type=query_type, search_field=search_field
        )

        if not settings.COMMON_DISABLE_LOCAL_STORAGE:
            index = self._get_or_create_index(
                search_model=search_field.search_model
            )

            if isinstance(search_field, SearchFieldVirtualAllFields):
                parser = MultifieldParser(
                    [
                        search_field.field_name for search_field in search_field.field_composition
                    ], schema=index.schema, group=OrGroup
                )
                search_field_queries = []

                for search_field in search_field.field_composition:
                    try:
                        search_string = query_type.resolve_for_backend(
                            is_quoted_value=is_quoted_value,
                            is_raw_value=is_raw_value, search_backend=self,
                            search_field=search_field, value=value,
                            extra_kwargs={
                                'parser': parser
                            }
                        )
                    except DynamicSearchValueTransformationError:
                        """Skip the search field."""
                    else:
                        if search_string is not None:
                            search_field_queries.append(search_string)

                query = parser.parse(
                    ' '.join(search_field_queries)
                )
            else:
                parser = qparser.QueryParser(
                    fieldname=search_field.field_name, schema=index.schema
                )

                try:
                    search_string = query_type.resolve_for_backend(
                        is_quoted_value=is_quoted_value,
                        is_raw_value=is_raw_value, search_backend=self,
                        search_field=search_field, value=value,
                        extra_kwargs={
                            'parser': parser
                        }
                    )
                except DynamicSearchValueTransformationError:
                    return ()
                else:
                    if search_string is None:
                        return ()

                logger.debug('search_string: %s', search_string)

                query = parser.parse(text=search_string)

            return self._do_query_resolve(index=index, query=query)
        else:
            return ()

    def _update_mappings(self, search_model=None):
        if search_model:
            search_models = (search_model,)
        else:
            search_models = SearchModel.all()

        if not settings.COMMON_DISABLE_LOCAL_STORAGE:
            for search_model in search_models:
                self._get_or_create_index(search_model=search_model)

    def deindex_instance(self, instance):
        try:
            lock = LockingBackend.get_backend().acquire_lock(
                name=TEXT_LOCK_INSTANCE_DEINDEX
            )
        except LockError:
            raise
        else:
            try:
                search_model = SearchModel.get_for_model(instance=instance)
                index = self._get_or_create_index(search_model=search_model)

                if not settings.COMMON_DISABLE_LOCAL_STORAGE:
                    with index.writer(**self.writer_kwargs) as writer:
                        writer.delete_by_term(
                            'id', str(instance.pk)
                        )
            finally:
                lock.release()

    def do_native_type_conversion(self, value):
        if isinstance(value, (list, tuple)):
            return ' '.join(value)
        else:
            return value

    def index_instance(self, instance, exclude_model=None, exclude_kwargs=None):
        try:
            lock = LockingBackend.get_backend().acquire_lock(
                name=TEXT_LOCK_INSTANCE_INDEX
            )
        except LockError:
            raise
        else:
            try:
                search_model = SearchModel.get_for_model(instance=instance)
                if not settings.COMMON_DISABLE_LOCAL_STORAGE:
                    with self._get_writer(search_model=search_model) as writer:
                        try:
                            writer.delete_by_term(
                                'id', str(instance.pk)
                            )
                        except Exception as exception:
                            # The parenthesis is used to define a multi
                            # line error message not a translatable string.
                            error_text = (
                                'Unexpected exception while '
                                'deleting search object id: {id}, '
                                'search model: {search_model}, '
                                'raw data: {raw_data}, '
                                'field map: {field_map}; '
                                '{exception}'
                            ).format(
                                exception=exception,
                                field_map=self.get_resolved_field_type_map(
                                    search_model=search_model
                                ), id=instance.pk,
                                raw_data=instance.__dict__,
                                search_model=search_model.full_name
                            )

                            logger.error(error_text, exc_info=True)
                            raise DynamicSearchBackendException(
                                error_text
                            ) from exception
                        else:
                            kwargs = search_model.populate(
                                search_backend=self, instance=instance,
                                exclude_model=exclude_model,
                                exclude_kwargs=exclude_kwargs
                            )

                            try:
                                writer.add_document(**kwargs)
                            except Exception as exception:
                                # The parenthesis is used to define a multi
                                # line error message not a translatable
                                # string.
                                error_text = (
                                    'Unexpected exception while '
                                    'indexing search object id: {id}, '
                                    'search model: {search_model}, '
                                    'index data: {index_data}, '
                                    'raw data: {raw_data}, '
                                    'field map: {field_map}; '
                                    '{exception}'
                                ).format(
                                    exception=exception,
                                    field_map=self.get_resolved_field_type_map(
                                        search_model=search_model
                                    ), id=instance.pk, index_data=kwargs,
                                    raw_data=instance.__dict__,
                                    search_model=search_model.full_name
                                )

                                logger.error(error_text, exc_info=True)
                                raise DynamicSearchBackendException(
                                    error_text
                                ) from exception

            except whoosh.index.LockError:
                raise DynamicSearchRetry
            finally:
                lock.release()

    def index_instances(self, search_model, id_list):
        queryset = search_model.get_queryset()
        queryset = queryset.filter(pk__in=id_list)

        try:
            lock = LockingBackend.get_backend().acquire_lock(
                name=TEXT_LOCK_INSTANCE_INDEX
            )
        except LockError:
            raise
        else:
            try:
                if not settings.COMMON_DISABLE_LOCAL_STORAGE:
                    index = self._get_or_create_index(search_model=search_model)

                    writer = BufferedWriter(index=index)
                    try:
                        for instance in queryset:
                            kwargs = search_model.populate(
                                search_backend=self, instance=instance
                            )

                            try:
                                writer.update_document(**kwargs)
                            except Exception as exception:
                                # The parenthesis is used to define a multi
                                # line error message not a translatable
                                # string.
                                error_text = (
                                    'Unexpected exception while '
                                    'indexing search model: {search_model}, '
                                    'id_list: {id_list}, '
                                    'index data: {index_data}, '
                                    'raw data: {raw_data}, '
                                    'field map: {field_map}; '
                                    '{exception}'
                                ).format(
                                    exception=exception,
                                    field_map=self.get_resolved_field_type_map(
                                        search_model=search_model
                                    ), id_list=id_list, index_data=kwargs,
                                    raw_data=instance.__dict__,
                                    search_model=search_model.full_name
                                )

                                logger.error(error_text, exc_info=True)
                                raise DynamicSearchBackendException(
                                    error_text
                                ) from exception
                    finally:
                        writer.close()
            except whoosh.index.LockError:
                raise DynamicSearchRetry
            finally:
                lock.release()

    def reset(self, search_model=None):
        self.tear_down(search_model=search_model)
        self._update_mappings(search_model=search_model)

    def tear_down(self, search_model=None):
        if search_model:
            search_models = (search_model,)
        else:
            search_models = SearchModel.all()

        if not settings.COMMON_DISABLE_LOCAL_STORAGE:
            for search_model in search_models:
                self._clear_search_model_index(search_model=search_model)

    def test_mode_stop(self):
        self.__class__._local_attribute_backend_temporary_directory.cleanup()
