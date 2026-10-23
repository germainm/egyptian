import logging

from django.utils.translation import gettext_lazy as _

from .exceptions import (
    DynamicSearchException, DynamicSearchQueryError,
    DynamicSearchValueTransformationError
)

logger = logging.getLogger(name=__name__)


class BackendQueryType:
    _registry = {}

    @classmethod
    def get_for_query_type(cls, search_backend, query_type):
        search_backend_dictionary = cls._registry.get(
            search_backend, {}
        )

        return search_backend_dictionary[query_type]

    @classmethod
    def register(cls, klass, search_backend):
        cls._registry.setdefault(
            search_backend, {}
        )

        search_backend_dictionary = cls._registry[search_backend]

        if klass.query_type in search_backend_dictionary:
            raise DynamicSearchException(
                'Backend query type `{}` is attempting to register to query '
                'type `{}` which is already registered to backend query '
                'type `{}`.'.format(
                    klass, klass.query_type,
                    search_backend_dictionary[klass.query_type]
                )
            )

        search_backend_dictionary[klass.query_type] = klass

    def __init__(
        self, is_quoted_value, search_backend, search_field, value,
        extra_kwargs=None
    ):
        self.extra_kwargs = extra_kwargs or {}
        self.is_quoted_value = is_quoted_value
        self.search_backend = search_backend
        self.search_field = search_field
        self.value = value

    def get_search_backend_field_type(self):
        return self.search_backend.get_search_field_backend_field_type(
            search_field=self.search_field
        )


class QueryTypeMetaclass(type):
    def __str__(cls):
        return str(cls.label)


class QueryType(metaclass=QueryTypeMetaclass):
    _default_klass = None
    _registry = []

    @classmethod
    def all(cls):
        return cls._registry

    @classmethod
    def check(cls, value):
        if value.startswith(cls.alias):
            return value[
                len(cls.alias):
            ]

    @classmethod
    def check_all(cls, value):
        for klass in cls.all():
            text = klass.check(value=value)
            if text is not None:
                return (klass, text)

        if cls._default_klass:
            return (cls._default_klass, value)
        else:
            raise DynamicSearchQueryError(
                'Query alias does not match any know query type class.'
            )

    @classmethod
    def do_value_process(
        cls, is_raw_value, search_backend, search_field, value
    ):
        if is_raw_value:
            return value
        else:
            return search_field.do_value_search_transform(
                search_backend=search_backend, value=value
            )

    @classmethod
    def get_default(cls):
        return cls._default_klass

    @classmethod
    def get_for_backend(cls, search_backend):
        return BackendQueryType.get_for_query_type(
            query_type=cls, search_backend=search_backend
        )

    @classmethod
    def resolve_for_backend(
        cls, is_quoted_value, is_raw_value, search_backend, search_field,
        value, extra_kwargs=None
    ):
        extra_kwargs = extra_kwargs or {}

        try:
            backend_query_type_class = cls.get_for_backend(
                search_backend=search_backend.__class__
            )
        except KeyError:
            raise DynamicSearchQueryError(
                'Query type `{}` is valid for field name `{}` but it is '
                'not implemented or registered by the backend.'.format(
                    cls, search_field.field_name
                )
            )
        else:
            if not value and not is_quoted_value:
                value = None

            try:
                value = cls.do_value_process(
                    is_raw_value=is_raw_value, search_backend=search_backend,
                    search_field=search_field, value=value
                )
            except DynamicSearchValueTransformationError as exception:
                logger.warning(
                    'Unable to convert value `{}` to the appropriate '
                    'data type to perform the search. Reason: {}'.format(
                        value, exception
                    )
                )
                raise
            else:
                backend_query_type = backend_query_type_class(
                    extra_kwargs=extra_kwargs,
                    is_quoted_value=is_quoted_value,
                    search_backend=search_backend, search_field=search_field,
                    value=value
                )

                return backend_query_type.do_resolve()

    @classmethod
    def register(cls, klass):
        cls._registry.append(klass)

    @classmethod
    def set_default(cls, klass):
        cls._default_klass = klass


class QueryTypeExact(QueryType):
    alias = '='
    label = _(message='Exact')
    name = 'EXACT'


class QueryTypeFuzzy(QueryType):
    alias = '~'
    label = _(message='Fuzzy')
    name = 'FUZZY'


class QueryTypeGreaterThan(QueryType):
    alias = '>'
    label = _(message='Greater than')
    name = 'GREATERTHAN'


class QueryTypeGreaterThanOrEqual(QueryType):
    alias = '>='
    label = _(message='Greater than or equal')
    name = 'GREATERTHANOREQUAL'


class QueryTypeLessThan(QueryType):
    alias = '<'
    label = _(message='Less than')
    name = 'LESSTHAN'


class QueryTypeLessThanOrEqual(QueryType):
    alias = '<='
    label = _(message='Less than or equal')
    name = 'LESSTHANOREQUAL'


class QueryTypePartial(QueryType):
    alias = '*'
    label = _(message='Partial')
    name = 'PARTIAL'


class QueryTypeRange(QueryType):
    alias = '[]'
    label = _(message='Range')
    name = 'RANGE'

    @classmethod
    def do_value_process(
        cls, is_raw_value, search_backend, search_field, value
    ):
        if is_raw_value:
            return value
        else:
            parts = []
            try:
                items = value.split('..')
            except AttributeError:
                raise DynamicSearchValueTransformationError(
                    'Unable to parse range term `{}`'.format(value)
                )
            else:
                if len(items) != 2:
                    raise DynamicSearchValueTransformationError(
                        'Invalid number of arguments for range `{}`'.format(
                            value
                        )
                    )
                for item in items:
                    parts.append(
                        search_field.do_value_search_transform(
                            search_backend=search_backend, value=item
                        )
                    )
                return parts


class QueryTypeRangeExclusive(QueryTypeRange):
    alias = '{}'
    label = _(message='Range exclusive')
    name = 'RANGEEXCLUSIVE'


class QueryTypeRegularExpression(QueryType):
    alias = '%'
    label = _(message='Regular expression')
    name = 'REGULAREXPRESSION'


QueryType.register(klass=QueryTypeExact)
QueryType.register(klass=QueryTypeFuzzy)
QueryType.register(klass=QueryTypeGreaterThanOrEqual)
QueryType.register(klass=QueryTypeGreaterThan)
QueryType.register(klass=QueryTypeLessThanOrEqual)
QueryType.register(klass=QueryTypeLessThan)
QueryType.register(klass=QueryTypePartial)
QueryType.register(klass=QueryTypeRange)
QueryType.register(klass=QueryTypeRangeExclusive)
QueryType.register(klass=QueryTypeRegularExpression)

QueryType.set_default(klass=QueryTypePartial)
