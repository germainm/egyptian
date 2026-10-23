from functools import cache
import logging

from django.core.exceptions import ImproperlyConfigured
from django.template import RequestContext, Variable, VariableDoesNotExist

from .class_mixins import TemplateObjectMixin
from .links import ResolvedLink
from .utils import get_current_view_name

logger = logging.getLogger(name=__name__)


class Menu(TemplateObjectMixin):
    _registry = {}

    @staticmethod
    def get_result_label(item):
        if isinstance(item, ResolvedLink):
            return str(item.link.text)
        else:
            return str(item.label)

    @classmethod
    def get(cls, name):
        return cls._registry[name]

    @classmethod
    def remove(cls, name):
        del cls._registry[name]

    def __init__(
        self, name, cache_class_associations=True, condition=None, icon=None,
        label=None, non_sorted_sources=None, title=None
    ):
        if name in self.__class__._registry:
            raise Exception('A menu with this name already exists')

        self.cache_class_associations = cache_class_associations
        self.bound_links = {}
        self.condition = condition
        self.excluded_links = {}
        self._icon = icon
        self.label = label
        self.link_positions = {}
        self.name = name
        self.non_sorted_sources = non_sorted_sources or []
        self.proxy_exclusions = set()
        self.title = title
        self.unbound_links = {}
        self.__class__._registry[name] = self

    def __repr__(self):
        return '<Menu: {}>'.format(self.name)

    def _map_links_to_source(
        self, links, source, map_variable, position=None
    ):
        source_links = getattr(self, map_variable).setdefault(
            source, []
        )

        position = position or len(source_links)

        for link_index, link in enumerate(iterable=links):
            source_links.append(link)
            self.link_positions[link] = position + link_index

    def add_proxy_exclusion(self, source):
        self.proxy_exclusions.add(source)

    def add_unsorted_source(self, source):
        self.non_sorted_sources.append(source)

    def bind_links(self, links, exclude=None, sources=None, position=None):
        try:
            for source in sources:
                self._map_links_to_source(
                    links=links, map_variable='bound_links',
                    position=position, source=source
                )
            for source in exclude:
                self._map_links_to_source(
                    links=links, map_variable='excluded_links',
                    position=position, source=source
                )
        except TypeError:
            self._map_links_to_source(
                links=links, map_variable='bound_links',
                position=position, source=sources
            )

    def get_icon(self, context):
        return self._icon

    def do_matched_links_update(
        self, matched_links, bound_object, unbound_object, excluded_object
    ):

        matched_links.update(
            set(
                self.bound_links.get(
                    bound_object, ()
                )
            ) - set(
                self.unbound_links.get(
                    unbound_object, ()
                )
            ) - set(
                self.unbound_links.get(
                    None, ()
                )
            ) - set(
                self.excluded_links.get(
                    excluded_object, ()
                )
            )
        )

        return matched_links

    @cache
    def get_links_for_class_cached(self, resolved_navigation_object_class):
        return self.get_links_for_class_non_cached(
            resolved_navigation_object_class=resolved_navigation_object_class
        )

    def get_links_for_class_non_cached(self, resolved_navigation_object_class):
        matched_links = set()

        try:
            mro = resolved_navigation_object_class.__mro__
        except AttributeError:
            bound_object = resolved_navigation_object_class
            excluded_object = resolved_navigation_object_class
            unbound_object = resolved_navigation_object_class

            matched_links = self.do_matched_links_update(
                bound_object=bound_object, excluded_object=excluded_object,
                matched_links=matched_links, unbound_object=unbound_object
            )
        else:
            model = resolved_navigation_object_class
            try:
                proxy_parent_model = model._meta.proxy_for_model
            except AttributeError:
                """It's not a model, treat as a generic class."""

                for super_class in mro[:-1]:
                    bound_object = super_class
                    excluded_object = resolved_navigation_object_class
                    unbound_object = super_class

                    matched_links = self.do_matched_links_update(
                        bound_object=bound_object,
                        excluded_object=excluded_object,
                        matched_links=matched_links,
                        unbound_object=unbound_object
                    )
            else:
                matched_links = self.do_matched_links_update(
                    bound_object=model,
                    excluded_object=model,
                    matched_links=matched_links,
                    unbound_object=model
                )

                if proxy_parent_model:
                    if model not in self.proxy_exclusions:
                        matched_links = self.do_matched_links_update(
                            bound_object=proxy_parent_model,
                            excluded_object=model,
                            matched_links=matched_links,
                            unbound_object=proxy_parent_model
                        )

        return matched_links

    def get_navigation_object_class(self, resolved_navigation_object):
        if resolved_navigation_object is None:
            return None
        elif isinstance(resolved_navigation_object, str):
            return resolved_navigation_object
        else:
            try:
                resolved_navigation_object.query
            except AttributeError:
                try:
                    item = resolved_navigation_object[0]
                except TypeError:
                    try:
                        model = resolved_navigation_object._meta.model
                    except AttributeError:
                        return resolved_navigation_object.__class__
                    else:
                        return model
                else:
                    return self.get_navigation_object_class(
                        resolved_navigation_object=item
                    )
            else:
                model = resolved_navigation_object.model

                return self.get_navigation_object_class(
                    resolved_navigation_object=model
                )

    def get_resolved_navigation_object_list(self, context, source):
        resolved_navigation_object_list = []

        if source:
            resolved_navigation_object_list = [source]
        else:
            navigation_object_list = context.get(
                'navigation_object_list', ('object',)
            )

            logger.debug(
                'navigation_object_list: %s', navigation_object_list
            )

            for navigation_object in navigation_object_list:
                try:
                    resolved_variable = Variable(
                        var=navigation_object
                    ).resolve(context=context)
                except VariableDoesNotExist:
                    """Non fatal. Proceed with next variable name in list."""
                else:
                    resolved_navigation_object_list.append(
                        resolved_variable
                    )

        logger.debug(
            'resolved_navigation_object_list: %s', str(
                resolved_navigation_object_list
            )
        )
        return resolved_navigation_object_list

    def get_result_position(self, item):
        if isinstance(item, ResolvedLink):
            return self.link_positions.get(item.link, 0)
        else:
            return self.link_positions.get(item, 0) or 0

    def resolve(
        self, context=None, request=None, source=None, sort_results=False
    ):
        result = []

        if self.cache_class_associations:
            function_get_links_for_class = self.get_links_for_class_cached
        else:
            function_get_links_for_class = self.get_links_for_class_non_cached

        if not context and not request:
            raise ImproperlyConfigured(
                'Must provide a context or a request in order to resolve '
                'the menu.'
            )

        if not context:
            context = RequestContext(request=request)

        if not self.check_condition(context=context):
            return result

        try:
            request = self.get_request(context=context, request=request)
        except VariableDoesNotExist:
            return result

        current_view_name = get_current_view_name(request=request)
        if not current_view_name:
            return result

        resolved_navigation_object_list = self.get_resolved_navigation_object_list(
            context=context, source=source
        )

        for resolved_navigation_object in resolved_navigation_object_list:
            navigation_object_class = self.get_navigation_object_class(
                resolved_navigation_object=resolved_navigation_object
            )
            matched_links = function_get_links_for_class(
                resolved_navigation_object_class=navigation_object_class
            )

            result.extend(
                self.resolve_matched_links(
                    context=context,
                    matched_links=matched_links,
                    resolved_navigation_object=resolved_navigation_object,
                    as_resolved_object=True
                )
            )

        navigation_object_class = self.get_navigation_object_class(
            resolved_navigation_object=current_view_name
        )
        matched_links = function_get_links_for_class(
            resolved_navigation_object_class=navigation_object_class
        )

        result.extend(
            self.resolve_matched_links(
                context=context,
                matched_links=matched_links,
                resolved_navigation_object=current_view_name
            )
        )

        navigation_object_class = self.get_navigation_object_class(
            resolved_navigation_object=None
        )
        matched_links = function_get_links_for_class(
            resolved_navigation_object_class=navigation_object_class
        )

        result.extend(
            self.resolve_matched_links(
                context=context,
                matched_links=matched_links,
                resolved_navigation_object=None
            )
        )

        if result:
            unsorted_source = False
            for resolved_navigation_object in resolved_navigation_object_list:
                for source in self.non_sorted_sources:
                    if isinstance(resolved_navigation_object, source):
                        unsorted_source = True
                        break

            if sort_results and not unsorted_source:
                for link_group in result:
                    link_group['links'].sort(key=Menu.get_result_label)
            else:
                for link_group in result:
                    link_group['links'].sort(key=self.get_result_position)

        return result

    def resolve_matched_links(
        self, context, matched_links, resolved_navigation_object,
        as_resolved_object=False
    ):
        result = []

        object_resolved_links = []

        for link in matched_links:
            kwargs = {'context': context}

            if as_resolved_object:
                kwargs['resolved_object'] = resolved_navigation_object

            if isinstance(link, Menu):
                condition = link.check_condition(**kwargs)
                if condition:
                    object_resolved_links.append(link)
            else:
                resolved_link = link.resolve(**kwargs)
                if resolved_link:
                    object_resolved_links.append(resolved_link)

        if object_resolved_links:
            result.append(
                {
                    'links': object_resolved_links,
                    'object': resolved_navigation_object
                }
            )

        return result

    def unbind_links(self, links, sources=None):
        if sources is None:
            self._map_links_to_source(
                links=links, source=None, map_variable='unbound_links'
            )
        else:
            for source in sources:
                self._map_links_to_source(
                    links=links, source=source, map_variable='unbound_links'
                )

        self.get_links_for_class_cached.cache_clear()
