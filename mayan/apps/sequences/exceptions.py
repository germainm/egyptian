from rest_framework import status
from rest_framework.exceptions import APIException


class SequenceError(Exception):
    pass


class SequenceExhausted(SequenceError):
    pass


class SequenceValueCountInvalid(SequenceError):
    pass


class SequenceBackendArgumentError(SequenceError):
    pass


class SequenceExhaustedAPIError(APIException):
    default_code = 'sequence_exhausted'
    default_detail = 'The sequence is exhausted.'
    status_code = status.HTTP_409_CONFLICT
