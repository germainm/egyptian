from elasticsearch.dsl import Q, field

from ...search_query_types import (
    BackendQueryType, QueryTypeExact, QueryTypeFuzzy, QueryTypeGreaterThan,
    QueryTypeGreaterThanOrEqual, QueryTypeLessThan, QueryTypeLessThanOrEqual,
    QueryTypePartial, QueryTypeRange, QueryTypeRangeExclusive,
    QueryTypeRegularExpression
)

from .backend import ElasticsearchSearchBackend


class BackendQueryTypeExact(BackendQueryType):
    query_type = QueryTypeExact

    def do_resolve(self):
        if self.value is not None:
            if self.is_quoted_value:
                template = '"{}"'
            else:
                template = '{}'

            if not self.value:
                # Empty values cannot be quoted.
                template = '{}'

                if self.is_quoted_value:
                    if self.get_search_backend_field_type() == field.Text:
                        return Q(
                            'bool', must_not=(
                                Q(
                                    'wildcard',
                                    **{self.search_field.field_name: '*'}
                                )
                            )
                        )

            if self.is_quoted_value:
                return Q(
                    name_or_query='match_phrase', _expand__to_dot=False,
                    **{
                        self.search_field.field_name: template.format(self.value)
                    }
                )
            else:
                return Q(
                    name_or_query='match', _expand__to_dot=False,
                    **{
                        self.search_field.field_name: template.format(self.value)
                    }
                )


class BackendQueryFuzzy(BackendQueryType):
    query_type = QueryTypeFuzzy

    def do_resolve(self):
        if self.value is not None:
            return Q(
                name_or_query='fuzzy', _expand__to_dot=False,
                **{self.search_field.field_name: self.value}
            )


class BackendQueryTypeGreaterThan(BackendQueryType):
    query_type = QueryTypeGreaterThan

    def do_resolve(self):
        if self.value is not None:
            return Q(
                name_or_query='range', _expand__to_dot=False,
                **{
                    self.search_field.field_name: {'gt': self.value}
                }
            )


class BackendQueryTypeGreaterThanOrEqual(BackendQueryType):
    query_type = QueryTypeGreaterThanOrEqual

    def do_resolve(self):
        if self.value is not None:
            return Q(
                name_or_query='range', _expand__to_dot=False,
                **{
                    self.search_field.field_name: {'gte': self.value}
                }
            )


class BackendQueryTypeLessThan(BackendQueryType):
    query_type = QueryTypeLessThan

    def do_resolve(self):
        if self.value is not None:
            return Q(
                name_or_query='range', _expand__to_dot=False,
                **{
                    self.search_field.field_name: {'lt': self.value}
                }
            )


class BackendQueryTypeLessThanOrEqual(BackendQueryType):
    query_type = QueryTypeLessThanOrEqual

    def do_resolve(self):
        if self.value is not None:
            return Q(
                name_or_query='range', _expand__to_dot=False,
                **{
                    self.search_field.field_name: {'lte': self.value}
                }
            )


class BackendQueryTypePartial(BackendQueryType):
    query_type = QueryTypePartial

    # Characters that indicate the user explicitly wants a wildcard pattern.
    # If the value contains any of these, the wildcard query is preserved.
    WILDCARD_CHARS = ('*', '?')

    def _value_has_explicit_wildcard(self):
        return any(c in self.value for c in self.WILDCARD_CHARS)

    def do_resolve(self):
        if self.value is None:
            return None

        backend_field_type = self.get_search_backend_field_type()

        if backend_field_type == field.Date:
            # Date fields are not handled by partial search.
            return None

        if self.is_quoted_value:
            # Quoted value — preserve original match_phrase behaviour.
            return Q(
                name_or_query='match_phrase', _expand__to_dot=False,
                **{self.search_field.field_name: self.value}
            )

        if backend_field_type == field.Integer:
            # Integers do not support wildcard or full-text match.
            return None

        if self._value_has_explicit_wildcard():
            # The user explicitly typed a wildcard pattern (e.g. "factu*").
            # Preserve the wildcard query so the intent is respected.
            return Q(
                name_or_query='wildcard', _expand__to_dot=False,
                **{self.search_field.field_name: self.value}
            )

        # Default path — plain token with no explicit wildcard.
        #
        # Original behaviour: wildcard *value* — performs a full index scan
        # because the leading * prevents ES from using the inverted index.
        #
        # Optimized behaviour: match query — ES tokenizes the value through
        # the same analyser used at index time (accent fold, hyphen replace,
        # casefold) and resolves against the inverted index. Orders of
        # magnitude faster on large indices, and consistent with how the
        # data was stored.
        return Q(
            name_or_query='match', _expand__to_dot=False,
            **{self.search_field.field_name: self.value}
        )


class BackendQueryTypeRange(BackendQueryType):
    query_type = QueryTypeRange

    def do_resolve(self):
        if self.value is not None:
            return Q(
                name_or_query='range', _expand__to_dot=False,
                **{
                    self.search_field.field_name: {
                        'gte': self.value[0], 'lte': self.value[1]
                    }
                }
            )


class BackendQueryTypeRangeExclusive(BackendQueryType):
    query_type = QueryTypeRangeExclusive

    def do_resolve(self):
        if self.value is not None:
            return Q(
                name_or_query='range', _expand__to_dot=False,
                **{
                    self.search_field.field_name: {
                        'gt': self.value[0], 'lt': self.value[1]
                    }
                }
            )


class BackendQueryTypeRegularExpression(BackendQueryType):
    query_type = QueryTypeRegularExpression

    def do_resolve(self):
        if self.value is not None:
            return Q(
                name_or_query='regexp', _expand__to_dot=False,
                **{self.search_field.field_name: self.value}
            )


BackendQueryType.register(
    klass=BackendQueryTypeExact, search_backend=ElasticsearchSearchBackend
)
BackendQueryType.register(
    klass=BackendQueryFuzzy, search_backend=ElasticsearchSearchBackend
)
BackendQueryType.register(
    klass=BackendQueryTypeGreaterThan, search_backend=ElasticsearchSearchBackend
)
BackendQueryType.register(
    klass=BackendQueryTypeGreaterThanOrEqual,
    search_backend=ElasticsearchSearchBackend
)
BackendQueryType.register(
    klass=BackendQueryTypeLessThan, search_backend=ElasticsearchSearchBackend
)
BackendQueryType.register(
    klass=BackendQueryTypeLessThanOrEqual,
    search_backend=ElasticsearchSearchBackend
)
BackendQueryType.register(
    klass=BackendQueryTypePartial, search_backend=ElasticsearchSearchBackend
)
BackendQueryType.register(
    klass=BackendQueryTypeRange,
    search_backend=ElasticsearchSearchBackend
)
BackendQueryType.register(
    klass=BackendQueryTypeRangeExclusive,
    search_backend=ElasticsearchSearchBackend
)
BackendQueryType.register(
    klass=BackendQueryTypeRegularExpression,
    search_backend=ElasticsearchSearchBackend
)
