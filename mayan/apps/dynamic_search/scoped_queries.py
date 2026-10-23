import logging

from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from .exceptions import (
    DynamicSearchBackendException, DynamicSearchScopedQueryError
)
from .literals import (
    ERROR_TEXT_NO_RESULT_SCOPE, SCOPE_DELIMITER, SCOPE_MARKER,
    SCOPE_OPERATOR_CHOICES, SCOPE_RESULT_MARKER, TERM_MARKER_QUOTE
)
from .search_query_terms import QueryToken
from .search_query_types import QueryType
from .settings import (
    setting_query_results_limit, setting_query_results_limit_error
)

logger = logging.getLogger(name=__name__)


class ScopedQuery:
    scope_delimiter = SCOPE_DELIMITER
    scope_marker = SCOPE_MARKER

    def __init__(self, search_model):
        self.scope_entry_list = []
        self.search_model = search_model
        self.entry_point = None

    def __str__(self):
        return ', '.join(
            [
                str(scope_entry) for scope_entry in self.scope_entry_list
            ]
        )

    def do_resolve(self, search_backend):
        if self.entry_point:
            id_list = self.entry_point.do_resolve(
                search_backend=search_backend
            )
            if id_list is None:
                raise DynamicSearchScopedQueryError(
                    _(message=ERROR_TEXT_NO_RESULT_SCOPE)
                )
            else:
                return id_list
        else:
            raise DynamicSearchScopedQueryError(
                _(message=ERROR_TEXT_NO_RESULT_SCOPE)
            )

    def do_scope_entry_add(self, scope_entry):
        scope_entry.do_pre_add_callback()
        self.scope_entry_list.append(scope_entry)
        scope_entry.do_post_add_callback()

    def do_scope_entry_init(self, **kwargs):
        kwargs['scoped_query'] = self

        scope_entry = ScopedQueryEntry.init(**kwargs)
        self.do_scope_entry_add(scope_entry=scope_entry)

        return scope_entry

    def do_scope_solve(self, search_backend, scope_identifier):
        scope_entry = self.get_scope_entry_by_identifier(
            scope_identifier=scope_identifier
        )

        return scope_entry.do_resolve(search_backend=search_backend)

    def get_scope_entry_by_identifier(self, scope_identifier):
        for scope_entry in self.scope_entry_list:
            scope_entry_identifier = getattr(
                scope_entry, 'scope_identifier', None
            )
            if scope_entry_identifier is not None and scope_entry_identifier == scope_identifier:
                return scope_entry

        raise DynamicSearchScopedQueryError(
            'No scope found with identifier `{}`'.format(scope_identifier)
        )

    def get_scope_identifier_list(self):
        result = []

        for scope_entry in self.scope_entry_list:
            scope_entry_identifier = getattr(
                scope_entry, 'scope_identifier', None
            )
            if scope_entry_identifier:
                result.append(scope_entry_identifier)

        return result

    def get_term_list(self):
        if self.entry_point:
            term_list = self.entry_point.get_term_list()
        else:
            term_list = ()

        result = []

        for term in term_list:
            if term not in result:
                result.append(term)

        return result

    @property
    def is_empty(self):
        return all(
            scope_entry.is_empty for scope_entry in self.scope_entry_list
        )

    def to_explain(self):
        if self.entry_point:
            return self.entry_point.to_explain()
        else:
            return ''

    def to_string(self):
        scope_text_list = []
        for scope_entry in self.scope_entry_list:
            scope_text_list.append(
                scope_entry.to_string()
            )

        return '&'.join(scope_text_list)


class ScopedQueryEntry:
    _registry = []

    @classmethod
    def _check(cls, key, scoped_query, **kwargs):
        raise NotImplementedError

    @classmethod
    def all(cls):
        return cls._registry

    @classmethod
    def check(cls, scoped_query, **kwargs):
        cls.scoped_query = scoped_query
        check_kwargs = cls._check(**kwargs)
        if check_kwargs is not None:
            check_kwargs['scoped_query'] = scoped_query
            return check_kwargs

    @classmethod
    def init(cls, scoped_query, **kwargs):
        for klass in cls.all():
            check_kwargs = klass.check(scoped_query=scoped_query, **kwargs)
            if check_kwargs is not None:
                return klass(**check_kwargs)

        raise DynamicSearchScopedQueryError(
            'No query entry found that could handle the arguments: '
            '`{}`, verify the query format, the field name, and the '
            'value data type.'.format(kwargs)
        )

    @classmethod
    def register(cls, klass):
        cls._registry.append(klass)

    def __init__(self, scoped_query, **kwargs):
        self.scoped_query = scoped_query

    def do_post_add_callback(self):
        pass

    def do_pre_add_callback(self):
        pass

    def do_resolve(self, search_backend):
        raise NotImplementedError

    def do_template_render(self, template_name, context=None):
        context_final = self.get_template_context_defaults()

        context_final.update(
            context or {}
        )

        template_string = self.get_template(template_name=template_name)

        return template_string.format(**context_final)

    def get_template(self, template_name):
        return self.templates[template_name]

    def get_template_context_defaults(self):
        return {
            'scope_delimiter': self.scoped_query.scope_delimiter,
            'scope_marker': self.scoped_query.scope_marker
        }

    def get_template_explain_context(self):
        return {}

    def get_template_key_context(self):
        return {}

    def get_template_value_context(self):
        return {}

    def get_term_list(self):
        return ()

    @property
    def is_empty(self):
        return False

    def to_explain(self):
        return self.do_template_render(
            template_name='explain',
            context=self.get_template_explain_context()
        )

    def to_string(self):
        return '{key}={value}'.format(
            key=self.do_template_render(
                template_name='key',
                context=self.get_template_key_context()
            ),
            value=self.do_template_render(
                template_name='value',
                context=self.get_template_value_context()
            )
        )


class ScopedQueryEntryData(ScopedQueryEntry):
    def __init__(self, scope_identifier, **kwargs):
        super().__init__(**kwargs)
        self.scope_identifier = scope_identifier

    def do_pre_add_callback(self):
        self.do_scope_identifier_check()

    def do_scope_identifier_check(self):
        try:
            scope_entry = self.scoped_query.get_scope_entry_by_identifier(
                scope_identifier=self.scope_identifier
            )
        except DynamicSearchScopedQueryError:
            return
        else:
            raise DynamicSearchScopedQueryError(
                'Scope `{}` is already defined by entry `{}`.'.format(
                    self.scope_identifier, scope_entry.to_string()
                )
            )

    def get_template_key_context(self):
        return {'scope_identifier': self.scope_identifier}


class ScopedQueryEntryDataFilter(ScopedQueryEntryData):
    templates = {
        'explain': '{field_name} {query_type} {value}',
        'key': '{scope_marker}{scope_identifier}{scope_delimiter}{field_name}',
        'value': '{value}'
    }

    @classmethod
    def _check(cls, key, value):
        if key.startswith(cls.scoped_query.scope_marker):
            key = key[
                len(cls.scoped_query.scope_marker):
            ]

            try:
                scope_identifier, field_name = key.split(
                    cls.scoped_query.scope_delimiter, 1
                )
            except ValueError:
                return None

            any_field = any(
                field_name == search_field_name for search_field_name in cls.scoped_query.search_model.search_field_name_list
            )
            if any_field:
                tokens = QueryToken.do_query_parse(value=value)
                if len(tokens) > 0:
                    if len(tokens) > 1:
                        raise DynamicSearchScopedQueryError(
                            'Each scoped mush only query one term. Multiple '
                            'terms must be split into different scopes. '
                            'To query for multiple words use the symbol '
                            '`{}` to collapase the words into a single '
                            'term.'.format(
                                TERM_MARKER_QUOTE
                            )
                        )
                    else:
                        return {
                            'field_name': field_name,
                            'is_quoted_value': tokens[0].is_quoted,
                            'is_raw_value': tokens[0].is_raw,
                            'scope_identifier': scope_identifier,
                            'value': tokens[0].text
                        }

    def __init__(
        self, field_name, value, is_quoted_value=False, is_raw_value=False,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.field_name = field_name
        self.is_quoted_value = is_quoted_value
        self.is_raw_value = is_raw_value
        self.value = value

    def __str__(self):
        return 'Scope `{}` = query {}: {}'.format(
            self.scope_identifier, self.field_name, self.value
        )

    def do_resolve(self, search_backend):
        scope_limit = setting_query_results_limit.value
        scope_limit_triggered = False

        if self.value:
            query_type, value = QueryType.check_all(value=self.value)

            try:
                results = search_backend._search(
                    is_quoted_value=self.is_quoted_value,
                    is_raw_value=self.is_raw_value, query_type=query_type,
                    search_field=self.search_field, value=value
                )

                count = 0

                for item in results:
                    count += 1

                    if count > scope_limit and not scope_limit_triggered:
                        scope_limit_triggered = True
                        error_message = _(
                            message='Query results exceed the current '
                            'limit of %d. Results will not be reliable '
                            'if multiple scopes are used. Narrow down '
                            'the search criteria or increase the value '
                            'of the results limit setting `%s`.'
                        ) % (
                            setting_query_results_limit.value,
                            setting_query_results_limit.global_name
                        )

                        logger.warning(error_message)

                        if setting_query_results_limit_error.value:
                            raise DynamicSearchScopedQueryError(error_message)

                        break

                    yield item
            except DynamicSearchBackendException:
                """Raise `DynamicSearchBackendException` as is."""
                raise
            except Exception as exception:
                """Wrap any other exception raised by the backend."""
                raise DynamicSearchBackendException(
                    _(
                        message='Search backend error. Verify that the '
                        'search service is available and that the search '
                        'syntax is valid for the active search backend; %s'
                    ) % exception
                ) from exception
        else:
            return ()

    def get_template_explain_context(self):
        context = super().get_template_explain_context()

        query_type, value = QueryType.check_all(value=self.value)

        if self.is_quoted_value:
            value = '"{}"'.format(value)
        elif self.is_raw_value:
            value = '`{}`'.format(value)

        context.update(
            {
                'field_name': self.field_name,
                'query_type': query_type.name,
                'value': value
            }
        )
        return context

    def get_template_key_context(self):
        context = super().get_template_key_context()

        context.update(
            {'field_name': self.field_name}
        )

        return context

    def get_template_value_context(self):
        return {'value': self.value}

    def get_term_list(self):
        if self.is_empty:
            return ()
        else:
            query_type, value = QueryType.check_all(value=self.value)

            return (value,)

    @property
    def is_empty(self):
        return not self.value and not self.is_quoted_value and not self.is_raw_value

    @cached_property
    def search_field(self):
        return self.scoped_query.search_model.get_search_field(
            field_name=self.field_name
        )


class ScopedQueryEntryDataOperator(ScopedQueryEntryData):
    templates = {
        'explain': '{operator_with_operands}',
        'key': '{scope_marker}{scope_identifier}',
        'value': '{operator_text}{scope_delimiter}{operand_list}'
    }

    @classmethod
    def _check(cls, key, value):
        if key.startswith(cls.scoped_query.scope_marker):
            scope_identifier = key[len(cls.scoped_query.scope_marker):]

            parts = value.split(cls.scoped_query.scope_delimiter)

            if len(parts) >= 3:
                if any(
                    operator_text == parts[0] for operator_text in SCOPE_OPERATOR_CHOICES
                ):
                    return {
                        'operand_list': parts[1:],
                        'operator_text': parts[0],
                        'scope_identifier': scope_identifier
                    }

    def __init__(self, operand_list, operator_text, **kwargs):
        super().__init__(**kwargs)

        if len(operand_list) < 2:
            raise DynamicSearchScopedQueryError(
                'Invalid operator declaration. Must specify '
                'at least two source scopes.'
            )

        self.operand_list = operand_list
        self.operator_text = operator_text

        if self.scope_identifier in self.operand_list:
            raise DynamicSearchScopedQueryError(
                'Operator scope `{}` is trying to resolve an operand '
                'with the same scope identifier. Self references are '
                'invalid. Verify the scope identifiers '
                'of the query.'.format(self.scope_identifier)
            )

    def __str__(self):
        return 'Scope `{}` = operator {}: {}'.format(
            self.scope_identifier, self.operator_text, self.operand_list
        )

    def do_resolve(self, search_backend):
        result = None

        for scope_child in self.operand_list:
            id_list = self.scoped_query.do_scope_solve(
                scope_identifier=scope_child,
                search_backend=search_backend
            )

            if result is None:
                result = id_list
            else:
                result = self.operator_function(result, id_list)

        return result

    def get_template_explain_context(self):
        context = super().get_template_explain_context()

        result = []

        for operand in self.operand_list:
            scope_entry = self.scoped_query.get_scope_entry_by_identifier(
                scope_identifier=operand
            )
            result.append(
                scope_entry.to_explain()
            )

        operator_with_operands = ' {} '.format(self.operator_text).join(
            result
        )

        context.update(
            {
                'operator_with_operands': '( {} )'.format(
                    operator_with_operands
                )
            }
        )
        return context

    def get_template_key_context(self):
        context = super().get_template_key_context()

        context.update(
            {
                'scope_identifier': self.scope_identifier
            }
        )

        return context

    def get_template_value_context(self):
        return {
            'operator_text': self.operator_text,
            'operand_list': self.scoped_query.scope_delimiter.join(
                self.operand_list
            )
        }

    def get_term_list(self):
        result = []

        for operand in self.operand_list:
            scope_entry = self.scoped_query.get_scope_entry_by_identifier(
                scope_identifier=operand
            )
            result.extend(
                scope_entry.get_term_list()
            )

        return result

    @property
    def operator_function(self):
        return SCOPE_OPERATOR_CHOICES.get(self.operator_text)


class ScopedQueryEntryControl(ScopedQueryEntry):
    pass


class ScopedQueryEntryControlResult(ScopedQueryEntryControl):
    templates = {
        'explain': '{scope_entry}',
        'key': '{scope_marker}{scope_result_marker}',
        'value': '{result_scope_identifier}'
    }

    @classmethod
    def _check(cls, key, value):
        if key == '{}{}'.format(
            cls.scoped_query.scope_marker, SCOPE_RESULT_MARKER
        ):
            return {'result_scope_identifier': value}

    def __init__(self, result_scope_identifier, **kwargs):
        super().__init__(**kwargs)
        self.result_scope_identifier = result_scope_identifier

    def __str__(self):
        return 'Result: {}'.format(self.result_scope_identifier)

    def do_post_add_callback(self):
        self.scoped_query.entry_point = self

    def do_resolve(self, search_backend):
        if self.result_scope_identifier:
            return self.scoped_query.do_scope_solve(
                scope_identifier=self.result_scope_identifier,
                search_backend=search_backend
            )

    def get_template_explain_context(self):
        context = super().get_template_explain_context()

        scope_entry = self.scoped_query.get_scope_entry_by_identifier(
            scope_identifier=self.result_scope_identifier
        )

        context.update(
            {
                'scope_entry': scope_entry.to_explain()
            }
        )

        return context

    def get_template_key_context(self):
        context = super().get_template_key_context()

        context.update(
            {
                'scope_result_marker': SCOPE_RESULT_MARKER
            }
        )

        return context

    def get_term_list(self):
        if self.result_scope_identifier:
            scope_entry = self.scoped_query.get_scope_entry_by_identifier(
                scope_identifier=self.result_scope_identifier
            )

            return scope_entry.get_term_list()
        else:
            return ()

    def get_template_value_context(self):
        context = super().get_template_value_context()

        context.update(
            {
                'result_scope_identifier': self.result_scope_identifier,
                'scope_result_marker': SCOPE_RESULT_MARKER
            }
        )

        return context


ScopedQueryEntry.register(klass=ScopedQueryEntryDataOperator)
ScopedQueryEntry.register(klass=ScopedQueryEntryDataFilter)
ScopedQueryEntry.register(klass=ScopedQueryEntryControlResult)
