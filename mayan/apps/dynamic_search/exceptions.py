from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.exceptions import APIException


class DynamicSearchException(Exception):
    pass


class DynamicSearchBackendException(DynamicSearchException):
    pass


class DynamicSearchBackendResourceError(DynamicSearchBackendException):
    pass


class DynamicSearchInterpreterError(DynamicSearchException):
    pass


class DynamicSearchInterpreterUnknownSearchType(
    DynamicSearchInterpreterError
):
    pass


class DynamicSearchModelException(DynamicSearchException):
    pass


class DynamicSearchQueryError(DynamicSearchException):
    pass


class DynamicSearchRetry(DynamicSearchException):
    pass


class DynamicSearchScopedQueryError(DynamicSearchException):
    pass


class DynamicSearchValueTransformationError(DynamicSearchException):
    pass


class DynamicSearchAPIErrorServiceUnavailable(APIException):
    default_code = 'service_unavailable'
    default_detail = _(
        message='The search service is temporarily unavailable.'
    )
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
