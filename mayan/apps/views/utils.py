from django.template import Variable
from django.urls import resolve as django_resolve
from django.urls.base import get_script_prefix
from django.utils.http import url_has_allowed_host_and_scheme

from .literals import (
    META_KEY_ALTERNATE_REFERER, META_KEY_REFERER, URL_QUERY_POSITIVE_VALUES
)


def base64_padding_add(value):
    remainder = len(value) % 4

    if remainder == 0:
        return value

    padding_needed = 4 - remainder
    return '{}{}'.format(value, '=' * padding_needed)


def convert_to_id_list(items):
    return ','.join(
        map(str, items)
    )


def get_request_data(request):
    request_get_data = request.GET.dict()
    request_post_data = request.POST.dict()

    query_dict = request_get_data.copy()
    query_dict.update(request_post_data)

    return query_dict


def get_request_referer(request, default=None):
    alternate_referer = request.META.get(META_KEY_ALTERNATE_REFERER)

    if alternate_referer:
        return alternate_referer

    return request.META.get(META_KEY_REFERER, default)


def get_safe_redirect_url(request, url, default_url=None):
    if not url:
        return default_url

    is_allowed = url_has_allowed_host_and_scheme(
        allowed_hosts={
            request.get_host()
        }, require_https=request.is_secure(), url=url
    )

    if is_allowed:
        return url

    return default_url


def get_request_from_context(context):
    try:
        return context.request
    except AttributeError:
        return Variable(var='request').resolve(context=context)


def is_url_query_positive(value):
    if value is not None:
        return value.lower() in URL_QUERY_POSITIVE_VALUES


def request_is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def request_wants_json(request):
    accept_header = request.META.get('HTTP_ACCEPT', '')
    accept_entry_list = accept_header.split(',')
    first_accept_entry = accept_entry_list[0]
    first_media_type = first_accept_entry.split(';')[0].strip()

    return first_media_type == 'application/json'


def resolve(path, urlconf=None):
    path = '/{}'.format(
        path.replace(
            get_script_prefix(), '', 1
        )
    )
    return django_resolve(path=path, urlconf=urlconf)
