from mayan.apps.views.utils import is_url_query_positive

from .exceptions import (
    DynamicSearchInterpreterError, DynamicSearchInterpreterUnknownSearchType,
    DynamicSearchScopedQueryError
)
from .literals import MATCH_ALL_FIELD_NAME, SCOPE_MARKER
from .scoped_queries import (
    ScopedQuery, ScopedQueryEntryControlResult, ScopedQueryEntryDataFilter,
    ScopedQueryEntryDataOperator
)
from .search_query_terms import QueryTerm
from .settings import setting_default_operator


class SearchInterpreter:
    _registry = {}

    @classmethod
    def all(cls):
        sorted_keys = sorted(
            cls._registry.keys()
        )
        return [
            cls._registry[key] for key in sorted_keys
        ]

    @classmethod
    def init(cls, query, search_model, prefix=''):
        for klass in cls.all():
            checked_query = klass.check(prefix=prefix, query=query)

            if checked_query is not None:
                return klass(
                    query=checked_query, search_model=search_model,
                    prefix=''
                )

        raise DynamicSearchInterpreterUnknownSearchType(
            'No `SearchInterpreter` subclass available that can handle '
            'this search syntax.'
        )

    @classmethod
    def register(cls, klass, priority):
        if priority in cls._registry:
            raise DynamicSearchInterpreterError(
                'Search interpreter `{}` is already registered for '
                'priority `{}`.'.format(
                    cls._registry[priority], priority
                )
            )
        else:
            cls._registry[priority] = klass

    def __init__(self, query, search_model, prefix=''):
        self.prefix = prefix
        self.query = query
        self.scoped_query_class = ScopedQuery
        self.search_model = search_model

        self.search_field_names = [
            search_field.field_name for search_field in self.search_model.search_fields
        ]

    @classmethod
    def do_prefix_remove(cls, prefix, value):
        if value.startswith(prefix):
            return value[
                len(prefix):
            ]

    def do_query_decode(self, query=None):
        return self._do_query_decode(query=query)

    def do_resolve(self, search_backend):
        scoped_query = self.do_query_decode()

        return scoped_query.do_resolve(search_backend=search_backend)

    def get_scoped_query_instance(self):
        return self.scoped_query_class(search_model=self.search_model)

    def get_term_list(self):
        clean_query = self.do_query_cleanup()

        scoped_query = self.do_query_decode(query=clean_query)

        return scoped_query.get_term_list()

    @property
    def is_empty(self):
        return self.do_query_decode().is_empty

    def to_explain(self):
        clean_query = self.do_query_cleanup()

        scoped_query = self.do_query_decode(query=clean_query)
        return scoped_query.to_explain()

    def to_string(self):
        raise NotImplementedError


class SearchInterpreterAdvanced(SearchInterpreter):

    @classmethod
    def check(cls, query, prefix=''):
        result = {}
        for key, value in query.items():
            key = cls.do_prefix_remove(prefix=prefix, value=key)
            if key:
                if not key.startswith(SCOPE_MARKER):
                    result[key] = value

        if result:
            return result

    def _do_query_decode(self, query=None):
        if query is None:
            query = self.query.copy()

        query_match_all_value = query.pop(MATCH_ALL_FIELD_NAME, 'no')

        self.global_and_search = is_url_query_positive(
            value=query_match_all_value
        )

        if self.global_and_search:
            inter_field_operator = 'AND'
        else:
            inter_field_operator = 'OR'

        query_field_term_dictionary = QueryTerm.do_query_parse(query=query)

        scoped_query = self.get_scoped_query_instance()

        self.do_scope_search_compose(
            inter_field_operator=inter_field_operator,
            query_field_term_dictionary=query_field_term_dictionary,
            scoped_query=scoped_query
        )

        if self.result_scope is not None:
            result_scope_identifier = str(self.result_scope)

            scoped_query_entry = ScopedQueryEntryControlResult(
                result_scope_identifier=result_scope_identifier,
                scoped_query=scoped_query
            )
            scoped_query.do_scope_entry_add(scope_entry=scoped_query_entry)

        return scoped_query

    def do_resolve(self, search_backend):
        try:
            return super().do_resolve(search_backend=search_backend)
        except DynamicSearchScopedQueryError:
            if not self.result_scope:
                return self.search_model.get_queryset().none()
            else:
                raise

    def do_scope_search_compose(
        self, inter_field_operator, query_field_term_dictionary, scoped_query
    ):
        self.result_scope = None

        field_result_scope_list = []
        scope_id = 0

        for key, term_list in query_field_term_dictionary.items():
            field_scopes = []
            field_operator = setting_default_operator.value

            for term in term_list:
                if term.is_meta:
                    field_operator = term.text
                else:
                    scoped_query_entry = ScopedQueryEntryDataFilter(
                        field_name=key, is_quoted_value=term.is_quoted,
                        is_raw_value=term.is_raw,
                        scope_identifier=str(scope_id),
                        scoped_query=scoped_query, value=term.text
                    )
                    scoped_query.do_scope_entry_add(
                        scope_entry=scoped_query_entry
                    )

                    field_scopes.append(scope_id)
                    scope_id += 1

            if field_scopes:
                new_scope_id = self.do_scope_operators_add(
                    operator_text=field_operator, result_scope=scope_id,
                    scope_id_list=field_scopes, scoped_query=scoped_query
                )
                if new_scope_id is not None:
                    scope_id = new_scope_id + 1

                field_result_scope_list.append(scope_id - 1)

        if field_result_scope_list:
            self.result_scope = self.do_scope_operators_add(
                operator_text=inter_field_operator, result_scope=scope_id,
                scope_id_list=field_result_scope_list,
                scoped_query=scoped_query
            )

    def do_scope_operators_add(
        self, scope_id_list, scoped_query, result_scope, operator_text='AND'
    ):
        if scope_id_list:
            operand_left = scope_id_list[0]

            for scope_id in scope_id_list[1:]:
                operand_right = scope_id

                scoped_query_entry = ScopedQueryEntryDataOperator(
                    operand_list=(
                        str(operand_left), str(operand_right)
                    ),
                    operator_text=operator_text,
                    scope_identifier=str(result_scope),
                    scoped_query=scoped_query
                )
                scoped_query.do_scope_entry_add(
                    scope_entry=scoped_query_entry
                )

                operand_left = result_scope
                result_scope += 1

            return result_scope - 1

    def do_query_cleanup(self):
        result = {}

        scoped_query = self.get_scoped_query_instance()

        for key, value in self.query.items():
            if value:
                key = self.do_prefix_remove(prefix=self.prefix, value=key)

                if key in scoped_query.search_model.search_field_name_list or key == MATCH_ALL_FIELD_NAME:
                    result[key] = value

        return result

    def to_string(self):
        scoped_query = self.do_query_decode()
        return scoped_query.to_string()


class SearchInterpreterScoped(SearchInterpreter):
    @classmethod
    def check(cls, query, prefix=''):
        result = {}
        for key, value in query.items():
            key = cls.do_prefix_remove(prefix=prefix, value=key)
            if key:
                if key.startswith(SCOPE_MARKER):
                    result[key] = value

        if result:
            return result

    def _do_query_decode(self, query=None):
        if query is None:
            query = self.query

        scoped_query = self.get_scoped_query_instance()

        for key, value in query.items():
            scoped_query.do_scope_entry_init(key=key, value=value)

        return scoped_query

    def do_query_cleanup(self):
        result = {}
        scoped_query = self.get_scoped_query_instance()

        for key, value in self.query.items():
            if value:
                key = self.do_prefix_remove(prefix=self.prefix, value=key)
                if key:
                    try:
                        scoped_query.do_scope_entry_init(
                            key=key, value=value
                        )
                    except DynamicSearchScopedQueryError:
                        """Ignore and continue."""
                    else:
                        result[key] = value

        return result

    def to_string(self):
        scoped_query = self.do_query_decode()
        return scoped_query.to_string()


SearchInterpreter.register(klass=SearchInterpreterAdvanced, priority=1)
SearchInterpreter.register(klass=SearchInterpreterScoped, priority=0)
