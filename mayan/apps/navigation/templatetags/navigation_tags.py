from django.template import Library
from django.utils.module_loading import import_string

from ..literals import TEXT_HTML_CLASS_MODAL_LINK
from ..menus import Menu
from ..source_columns import SourceColumn

register = Library()


@register.simple_tag(name='navigation_get_modal_link_class')
def tag_navigation_get_modal_link_class():
    return TEXT_HTML_CLASS_MODAL_LINK


def _navigation_resolve_menu(context, name, source=None, sort_results=None):
    result = []

    menu = Menu.get(name)
    link_groups = menu.resolve(
        context=context, source=source, sort_results=sort_results
    )

    if link_groups:
        result.append(
            {'link_groups': link_groups, 'menu': menu}
        )

    return result


@register.simple_tag(
    name='navigation_get_is_active_sort_field', takes_context=True
)
def tag_navigation_get_is_active_sort_field(context, column, reverse=None):
    return column.get_is_active_sort_field(context=context, reverse=reverse)


@register.simple_tag(name='navigation_get_link')
def tag_navigation_get_link(dotted_path):
    return import_string(dotted_path=dotted_path)


@register.simple_tag(
    name='navigation_get_sort_field_querystring', takes_context=True
)
def tag_navigation_get_sort_field_querystring(
    context, column, order=None, single_column=None
):
    return column.get_sort_field_querystring(
        context=context, order=order, single_column=single_column
    )


@register.simple_tag(name='navigation_get_source_columns')
def tag_navigation_get_source_columns(
    source, exclude_identifier=False, names=None, only_identifier=False
):
    return SourceColumn.get_for_source(
        source=source, exclude_identifier=exclude_identifier,
        names=names, only_identifier=only_identifier
    )


@register.simple_tag(name='navigation_get_source_columns_sortable')
def tag_navigation_get_source_columns_sortable(source):
    return SourceColumn.get_sortable_for_source(source=source)


@register.simple_tag(name='navigation_link_get_icon', takes_context=True)
def tag_navigation_link_get_icon(context, link):
    return link.get_icon(context=context)


@register.simple_tag(name='navigation_resolve_menu', takes_context=True)
def tag_navigation_resolve_menu(context, name, source=None, sort_results=None):
    return _navigation_resolve_menu(
        context=context, name=name, source=source, sort_results=sort_results
    )


@register.simple_tag(name='navigation_resolve_menus', takes_context=True)
def tag_navigation_resolve_menus(context, names, source=None, sort_results=None):
    result = []

    for name in names.split(','):
        result.extend(
            _navigation_resolve_menu(
                context=context, name=name, source=source, sort_results=sort_results
            )
        )

    return result


@register.simple_tag(name='navigation_resolved_menus_is_single_link')
def tag_navigation_resolved_menus_is_single_link(resolved_menus):
    if len(resolved_menus) == 1:
        if len(resolved_menus[0]['link_groups']) == 1:
            if len(resolved_menus[0]['link_groups'][0]['links']) == 1:
                return True


@register.simple_tag(
    name='navigation_source_column_get_sort_icon', takes_context=True
)
def tag_navigation_source_column_get_sort_icon(context, column):
    if column:
        result = column.get_sort_icon(context=context)
        return result
    else:
        return ''


@register.simple_tag(
    name='navigation_source_column_resolve', takes_context=True
)
def tag_navigation_source_column_resolve(context, column):
    if column:
        result = column.resolve(context=context)
        return result
    else:
        return ''
