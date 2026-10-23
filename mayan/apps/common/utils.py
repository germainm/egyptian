from functools import reduce
import itertools
import logging
import shlex
import types

from django.core.exceptions import FieldDoesNotExist
from django.db.models.constants import LOOKUP_SEP
from django.utils.text import slugify

from .compatibility import Iterable
from .exceptions import ResolverError, ResolverPipelineError

logger = logging.getLogger(name=__name__)


class ProgressBar:
    def __init__(
        self, total, prefix=None, suffix=None,
        decimal_places=1, length=100, fill_symbol='█', print_end='\r'
    ):
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.decimal_places = decimal_places
        self.length = length
        self.fill_symbol = fill_symbol
        self.print_end = print_end
        self.template_percent = '{{0:.{}f}}'.format(self.decimal_places)

    def update(self, index):
        percent = self.template_percent.format(
            index / self.total * 100.0
        )
        fill_size = int(self.length * index // self.total)
        bar = '{}{}'.format(
            self.fill_symbol * fill_size, '-' * (self.length - fill_size)
        )
        print(
            f'\r{self.prefix} |{bar}| {percent}% {self.suffix}',
            end=self.print_end
        )
        if index == self.total:
            print()


class Resolver:
    exceptions = ()

    def __init__(self, attribute, obj, kwargs, klass, resolver_extra_kwargs):
        self.attribute = attribute
        self.obj = obj
        self.kwargs = kwargs
        self.klass = klass
        self.resolver_extra_kwargs = resolver_extra_kwargs

    def resolve(self):
        try:
            return self._resolve()
        except self.exceptions:
            raise ResolverError

    def _resolve(self):
        raise NotImplementedError


class ResolverObjectAttribute(Resolver):
    exceptions = (TypeError,)

    def _resolve(self):
        return self.attribute(self.obj, **self.kwargs)


class ResolverGetattr(Resolver):
    exceptions = (AttributeError, TypeError,)

    def _resolve(self):
        return getattr(self.obj, self.attribute)


class ResolverFunction(Resolver):
    exceptions = (AttributeError, TypeError,)

    def _resolve(self):
        return getattr(self.obj, self.attribute)(**self.kwargs)


class ResolverDictionary(Resolver):
    exceptions = (TypeError,)

    def _resolve(self):
        return self.obj[self.attribute]


class ResolverList(Resolver):
    exceptions = (TypeError,)

    def _resolve(self):
        result = []
        for item in self.obj:
            result.append(
                self.klass.resolve(
                    attribute=self.attribute, kwargs=self.kwargs, obj=item,
                    resolver_extra_kwargs=self.resolver_extra_kwargs
                )
            )

        return result


class ResolverPipelineObjectAttribute:
    resolver_list = (
        ResolverDictionary, ResolverList, ResolverFunction,
        ResolverObjectAttribute, ResolverGetattr
    )

    @classmethod
    def resolve(
        cls, attribute, obj, resolver_extra_kwargs=None, kwargs=None
    ):
        kwargs = kwargs or {}
        resolver_extra_kwargs = resolver_extra_kwargs or {}

        if '.' in attribute:
            attribute_list = attribute.split('.')
        else:
            attribute_list = (attribute,)

        result = obj
        for attribute in attribute_list:
            for resolver in cls.resolver_list:
                try:
                    result = resolver(
                        attribute=attribute, klass=cls, kwargs=kwargs,
                        obj=result,
                        resolver_extra_kwargs=resolver_extra_kwargs
                    ).resolve()
                except ResolverError:
                    """Expected, try the next resolver in the list."""

            if result == obj:
                raise ResolverPipelineError(
                    'Unable to resolve attribute `{attribute}` of object `{obj}`'.format(
                        attribute=attribute, obj=obj
                    )
                )

        return result


class ResolverRelatedManager(Resolver):
    exceptions = (AttributeError, FieldDoesNotExist)

    def _resolve(self):
        model = self.resolver_extra_kwargs.get(
            'model', {}
        )
        exclude = self.resolver_extra_kwargs.get(
            'exclude', {}
        )

        field = self.obj._meta.get_field(field_name=self.attribute)

        if field.many_to_one:
            queryset = field.related_model._meta.default_manager.filter(
                **{field.remote_field.name: self.obj.pk}
            )

            if field.related_model == model:
                queryset = queryset.exclude(**exclude)

            return queryset
        elif field.many_to_many:
            if hasattr(field, 'get_filter_kwargs_for_object'):
                queryset = getattr(self.obj, field.attname)

                if queryset.model == model:
                    queryset = queryset.exclude(**exclude)
                else:
                    queryset = queryset.all()

                return queryset

        queryset = field.remote_field.model._meta.default_manager.filter(
            **{field.remote_field.name: self.obj.pk}
        )

        if field.related_model == model:
            queryset = queryset.exclude(**exclude)

        return queryset


class ResolverPipelineModelAttribute(ResolverPipelineObjectAttribute):
    resolver_list = (
        ResolverDictionary, ResolverList, ResolverRelatedManager,
        ResolverFunction, ResolverObjectAttribute, ResolverGetattr
    )

    @classmethod
    def resolve(
        cls, attribute, obj, kwargs=None, resolver_extra_kwargs=None
    ):
        attribute = attribute.replace(LOOKUP_SEP, '.')
        return super().resolve(
            attribute=attribute, kwargs=kwargs, obj=obj,
            resolver_extra_kwargs=resolver_extra_kwargs
        )


def any_to_bool(value):
    if isinstance(value, bool):
        return value

    normalized_value = str(value).lower()

    true_value_list = ('1', 'on', 't', 'true', 'y', 'yes')
    false_value_list = ('0', 'f', 'false', 'n', 'no', 'off')

    if normalized_value in true_value_list:
        return True
    elif normalized_value in false_value_list:
        return False
    else:
        raise ValueError(
            'Invalid truth value `{}`.'.format(value)
        )


def comma_splitter(string):
    splitter = shlex.shlex(string, posix=True)
    splitter.whitespace = ','
    splitter.whitespace_split = True
    splitter.commenters = ''
    return [
        str(e) for e in splitter
    ]


def convert_to_internal_name(value):
    slug = slugify(value=value)
    slug = slug.replace('-', '_')
    return slug


def deduplicate_dictionary_values(dictionary):
    result = {}

    for key, value in dictionary.items():
        value_test = value

        count = 1
        while True:
            if value_test in result.values():
                value_test = '{}_{}'.format(value, count)
                count += 1
            else:
                result[key] = value_test
                break

    return result


def flatten_list(value):
    if isinstance(value, (str, bytes)):
        yield value
    else:
        for item in value:
            if isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
                yield from flatten_list(value=item)
            else:
                if item is not None:
                    yield item
                else:
                    yield ''


def flatten_map(dictionary, result, prefix=None, separator='_'):
    if prefix:
        prefix_base = '{}{}'.format(prefix, separator)
    else:
        prefix_base = ''

    for key, value in dictionary.items():
        prefix_string = '{}{}'.format(prefix_base, key)

        if isinstance(value, dict):
            flatten_map(
                dictionary=value, prefix=prefix_string, result=result,
                separator=separator
            )
        else:
            result[prefix_string] = value


def flatten_object(obj, prefix=None, separator='_'):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if prefix is None:
                prefix_local = key
            else:
                prefix_local = '{prefix}{separator}{key}'.format(
                    key=key, prefix=prefix, separator=separator
                )

            yield from flatten_object(
                obj=value, prefix=prefix_local, separator=separator
            )
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            if prefix is None:
                prefix_local = index
            else:
                prefix_local = '{prefix}{separator}{index}'.format(
                    index=index, prefix=prefix, separator=separator
                )

            yield from flatten_object(
                obj=item, prefix=prefix_local, separator=separator
            )
    else:
        yield (prefix, obj)


def get_class_full_name(klass):
    return '{klass.__module__}.{klass.__qualname__}'.format(klass=klass)


def get_related_field(model, related_field_name):
    try:
        local_field_name, remaining_field_path = related_field_name.split(
            LOOKUP_SEP, 1
        )
    except ValueError:
        local_field_name = related_field_name
        remaining_field_path = None

    related_field = model._meta.get_field(field_name=local_field_name)

    if remaining_field_path:
        return get_related_field(
            model=related_field.related_model,
            related_field_name=remaining_field_path
        )

    return related_field


def group_iterator(iterable, group_size=None):
    group_size = group_size or 1

    iterable = iter(iterable)

    if group_size > 1:
        while True:
            chunk = tuple(
                itertools.islice(iterable, group_size)
            )
            if not chunk:
                break
            yield chunk
    else:
        yield from iterable


def interval_iterator(interval_list):
    for start, stop in interval_list:
        if stop > start:
            step = 1
        else:
            step = -1

        yield from range(start, stop + step, step)


def parse_range(range_string):
    interval_list = []

    for part in range_string.split(','):
        part = part.strip()

        if not part:
            continue

        if '-' in part:
            component_list = part.split('-')

            if len(component_list) != 2:
                raise ValueError(
                    'Invalid range `{}`; a range is a start number and a '
                    'stop number separated by a single dash.'.format(part)
                )

            start_string = component_list[0].strip()
            stop_string = component_list[1].strip()
        else:
            start_string = part
            stop_string = part

        try:
            start = int(start_string)
            stop = int(stop_string)
        except ValueError:
            raise ValueError(
                'Invalid range `{}`; it must be a number or two numbers '
                'separated by a dash.'.format(part)
            )

        interval_list.append(
            (start, stop)
        )

    return interval_iterator(interval_list=interval_list)


def resolve_attribute(attribute, obj, kwargs=None):
    if not kwargs:
        kwargs = {}

    try:
        return attribute(obj, **kwargs)
    except TypeError:
        try:
            return obj[attribute]
        except TypeError:
            try:
                result = reduce(
                    getattr, attribute.split('.'), obj
                )
                try:
                    return result(**kwargs)
                except (TypeError, ValueError):
                    return result
            except AttributeError:
                if LOOKUP_SEP in attribute:
                    attribute_replaced = attribute.replace(LOOKUP_SEP, '.')
                    return resolve_attribute(
                        attribute=attribute_replaced, kwargs=kwargs, obj=obj
                    )
                else:
                    raise


def return_attrib(obj, attrib, arguments=None):
    if isinstance(attrib, types.FunctionType):
        return attrib(obj)
    elif isinstance(
        obj, dict
    ) or isinstance(obj, dict):
        return obj[attrib]
    else:
        result = reduce(
            getattr, attrib.split('.'), obj
        )
        if isinstance(result, types.MethodType):
            if arguments:
                return result(**arguments)
            else:
                return result()
        else:
            return result


def return_related(instance, related_field):
    return reduce(
        getattr, related_field.split(LOOKUP_SEP), instance
    )
