import json
import logging

from django.template import Context, Library, VariableDoesNotExist
from django.template.defaultfilters import truncatechars
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from mayan.apps.appearance.settings import setting_max_title_length

from ..http import RequestQuery
from ..icons import icon_list_mode_items, icon_list_mode_list
from ..literals import (
    HEADER_NAME_ALTERNATE_REFERER, HEADER_NAME_MODAL,
    HEADER_NAME_PAGE_RELOAD, HEADER_NAME_REDIRECT_LOCATION,
    TEXT_LIST_AS_ITEMS_PARAMETER
)
from ..settings import setting_paging_argument
from ..utils import get_request_from_context

logger = logging.getLogger(name=__name__)
register = Library()


def get_request_query_from_context(context):
    """
    Build a `RequestQuery` from a template context. Returns `None` when the
    context does not provide a request, most probably a 500 in a test view.
    """
    try:
        request = get_request_from_context(context=context)
    except VariableDoesNotExist:
        logger.warning('No request variable, aborting request resolution')
        return None

    return RequestQuery(request=request)


def get_split_value_list(value):
    if not value:
        return ()

    result = []

    for entry in value.split(','):
        entry = entry.strip()

        if entry:
            result.append(entry)

    return tuple(result)


@register.simple_tag(name='views_calculate_title', takes_context=True)
def tag_views_calculate_title(context):
    title = ''
    title_full = ''

    if context.get('title'):
        title_full = context.get('title')
        title = truncatechars(
            title_full, arg=setting_max_title_length.value
        )
    else:
        if context.get('delete_view'):
            title = _(message='Confirm delete')
            title_full = title
        else:
            if context.get('form'):
                if context.get('object'):
                    title = _(message='Edit %s') % context.get('object')
                    title_full = title
                else:
                    title = _(message='Confirm')
                    title_full = title
            else:
                if context.get('read_only'):
                    title = _(message='Details for: %s') % context.get('object')
                    title_full = title
                else:
                    if context.get('object'):
                        title = _(message='Edit: %s') % context.get('object')
                        title_full = title
                    else:
                        if context.get('create_view') or context.get('form'):
                            title = _(message='Create')
                            title_full = title

    return {'title': title, 'title_full': title_full}


@register.simple_tag(name='views_get_header_names')
def tag_views_get_header_names():
    """
    Return the names of the headers used by the frontend contract, encoded
    as a JSON object. The frontend receives the names from the backend so
    they are defined in a single place instead of being repeated as string
    literals in the JavaScript layer.

    The keys are the identifiers used by the frontend and are therefore
    spelled the way the JavaScript layer spells its own properties. The
    values are the header names sent over the wire.
    """
    header_name_map = {
        'alternateReferer': HEADER_NAME_ALTERNATE_REFERER,
        'modal': HEADER_NAME_MODAL,
        'pageReload': HEADER_NAME_PAGE_RELOAD,
        'redirectLocation': HEADER_NAME_REDIRECT_LOCATION
    }

    result = json.dumps(obj=header_name_map)

    return mark_safe(s=result)


@register.simple_tag(name='views_get_list_mode_icon', takes_context=True)
def tag_views_get_list_mode_icon(context):
    if context.get('list_as_items', False):
        return icon_list_mode_list
    else:
        return icon_list_mode_items


@register.simple_tag(
    name='views_get_list_mode_querystring', takes_context=True
)
def tag_views_get_list_mode_querystring(context):
    list_as_items = context.get('list_as_items', False)

    if list_as_items:
        list_mode = 'list'
    else:
        list_mode = 'items'

    kwargs = {
        TEXT_LIST_AS_ITEMS_PARAMETER: list_mode
    }

    return tag_views_update_query_string(context=context, **kwargs)


@register.simple_tag(name='views_get_paging_query_string', takes_context=True)
def tag_views_get_paging_query_string(context, page_number):
    kwargs = {
        setting_paging_argument.value: page_number
    }
    return tag_views_update_query_string(context=context, **kwargs)


@register.simple_tag(name='views_get_proper_elided_page_range')
def tag_views_get_proper_elided_page_range(
    paginator, number, on_each_side=None, on_ends=None
):
    kwargs = {
        'number': number
    }

    if on_each_side:
        kwargs['on_each_side'] = on_each_side

    if on_ends:
        kwargs['on_ends'] = on_ends

    return paginator.get_elided_page_range(**kwargs)


@register.simple_tag(name='views_get_query_field_list', takes_context=True)
def tag_views_get_query_field_list(
    context, exclude_name_list=None, exclude_prefix_list=None
):
    """
    Return the query arguments of the current request as a list of field
    definitions, to be provided as fields of a form submitted using the GET
    method. Such a form replaces the query string of the resulting URL with
    its own data, discarding any argument it does not provide.

    The arguments the form provides on its own are excluded, by name or by
    prefix, as comma separated values.
    """
    request_query = get_request_query_from_context(context=context)

    if not request_query:
        return ()

    request_query.do_exclude(
        name_list=get_split_value_list(value=exclude_name_list),
        prefix_list=get_split_value_list(value=exclude_prefix_list)
    )

    return request_query.to_field_list()


@register.simple_tag(name='views_render_subtemplate', takes_context=True)
def tag_views_render_subtemplate(context, template_name, template_context):
    """
    Renders the specified template with the mixed parent and
    subtemplate contexts.
    """
    new_context = Context(
        context.flatten()
    )
    new_context.update(
        Context(template_context)
    )
    return get_template(template_name=template_name).render(
        context=new_context.flatten()
    )


@register.simple_tag(name='views_update_query_string', takes_context=True)
def tag_views_update_query_string(context, **kwargs):
    request_query = get_request_query_from_context(context=context)

    if not request_query:
        return ''

    request_query.do_update(**kwargs)

    return request_query.to_query_string()
