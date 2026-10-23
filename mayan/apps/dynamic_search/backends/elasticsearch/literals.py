from elasticsearch.dsl import field

from django.db import models

from ...search_query_types import (
    QueryTypeExact, QueryTypeFuzzy, QueryTypeGreaterThan,
    QueryTypeGreaterThanOrEqual, QueryTypeLessThan, QueryTypeLessThanOrEqual,
    QueryTypePartial, QueryTypeRange, QueryTypeRangeExclusive,
    QueryTypeRegularExpression
)
from ...value_transformations import (
    ValueTransformationAccentReplace, ValueTransformationAtReplace,
    ValueTransformationCasefold, ValueTransformationHyphenReplace,
    ValueTransformationHyphenStrip, ValueTransformationToBoolean,
    ValueTransformationToDateTime, ValueTransformationToDateTimeISOFormat,
    ValueTransformationToDateTimeTimestamp, ValueTransformationToInteger,
    ValueTransformationToString
)

DEFAULT_ELASTICSEARCH_HOSTS = ['https://127.0.0.1:9200']
DEFAULT_ELASTICSEARCH_INDICES_NAMESPACE = 'mayan'
DEFAULT_ELASTICSEARCH_INDICES_NAMESPACE_TEST = 'mayan-test'
DEFAULT_ELASTICSEARCH_POINT_IN_TIME_KEEP_ALIVE = '5m'
DEFAULT_ELASTICSEARCH_REFRESH_ON_SEARCH = False
DEFAULT_ELASTICSEARCH_SEARCH_PAGE_SIZE = 10000

DEFAULT_ELASTICSEARCH_SEARCH_RETRY_BACKOFF = 0.5
DEFAULT_ELASTICSEARCH_SEARCH_RETRY_BACKOFF_MAX = 2
DEFAULT_ELASTICSEARCH_SEARCH_RETRY_NUMBER = 0

ELASTICSEARCH_STATUS_CODE_TOO_MANY_REQUESTS = 429

"""
Integer field:

Django:
An integer. Values from -2147483648 to 2147483647 are safe in all
databases supported by Django.
https://docs.djangoproject.com/en/3.2/ref/models/fields/#integerfield

Django:
An integer. Values from -2147483648 to 2147483647 are safe in all
databases supported by Django.
https://docs.djangoproject.com/en/3.2/ref/models/fields/#integerfield

Elasticsearch:
A signed 32-bit integer with a minimum value of -2^31 (-2147483648)
and a maximum value of 2^31-1 (2147483647).
https://www.elastic.co/guide/en/elasticsearch/reference/current/number.html

Positive integer field:

Django:
Like an IntegerField, but must be either positive or zero (0).
Values from 0 to 2147483647 are safe in all databases supported by
Django. The value 0 is accepted for backward compatibility reasons.
https://docs.djangoproject.com/en/3.2/ref/models/fields/#positiveintegerfield
"""

DJANGO_TO_ELASTICSEARCH_FIELD_MAP = {
    models.AutoField: {
        'field': field.Integer,
        'query_type_list': [
            QueryTypeExact, QueryTypePartial, QueryTypeGreaterThan,
            QueryTypeGreaterThanOrEqual, QueryTypeLessThan,
            QueryTypeLessThanOrEqual, QueryTypeRange, QueryTypeRangeExclusive
        ],
        'transformations': {
            'index': [
                ValueTransformationToInteger
            ],
            'search': [
                ValueTransformationToInteger
            ]
        }
    },
    models.BigIntegerField: {
        'field': field.Long,
        'query_type_list': [
            QueryTypeExact, QueryTypeGreaterThan,
            QueryTypeGreaterThanOrEqual, QueryTypeLessThan,
            QueryTypeLessThanOrEqual, QueryTypeRange, QueryTypeRangeExclusive
        ],
        'transformations': {
            'search': [ValueTransformationToInteger]
        }
    },
    models.BooleanField: {
        'field': field.Boolean,
        'query_type_list': [
            QueryTypeExact
        ],
        'transformations': {
            'index': [
                ValueTransformationToString, ValueTransformationCasefold
            ],
            'search': [
                ValueTransformationToString, ValueTransformationToBoolean,
                ValueTransformationToString, ValueTransformationCasefold
            ]
        }
    },
    models.CharField: {
        'field': field.Text,
        'query_type_list': [
            QueryTypeExact, QueryTypeFuzzy, QueryTypePartial,
            QueryTypeRegularExpression, QueryTypeGreaterThan,
            QueryTypeGreaterThanOrEqual, QueryTypeLessThan,
            QueryTypeLessThanOrEqual
        ],
        'transformations': {
            'index': [
                ValueTransformationAccentReplace,
                ValueTransformationHyphenReplace, ValueTransformationCasefold
            ],
            'search': [
                ValueTransformationAccentReplace,
                ValueTransformationHyphenReplace, ValueTransformationCasefold
            ]
        }
    },
    models.DateTimeField: {
        'field': field.Date,
        'query_type_list': [
            QueryTypeExact, QueryTypeGreaterThan,
            QueryTypeGreaterThanOrEqual, QueryTypeLessThan,
            QueryTypeLessThanOrEqual, QueryTypeRange, QueryTypeRangeExclusive
        ],
        'transformations': {
            'index': [ValueTransformationToDateTimeISOFormat],
            'search': [
                ValueTransformationToDateTime,
                ValueTransformationToDateTimeTimestamp
            ]
        }
    },
    models.EmailField: {
        'field': field.Keyword,
        'query_type_list': [
            QueryTypeExact, QueryTypePartial
        ],
        'transformations': {
            'index': [
                ValueTransformationHyphenReplace,
                ValueTransformationAtReplace, ValueTransformationCasefold
            ],
            'search': [
                ValueTransformationHyphenReplace,
                ValueTransformationAtReplace, ValueTransformationCasefold
            ]
        }
    },
    models.IntegerField: {
        'field': field.Integer,
        'query_type_list': [
            QueryTypeExact, QueryTypeGreaterThan,
            QueryTypeGreaterThanOrEqual, QueryTypeLessThan,
            QueryTypeLessThanOrEqual, QueryTypeRange, QueryTypeRangeExclusive
        ],
        'transformations': {
            'search': [ValueTransformationToInteger]
        }
    },
    models.PositiveBigIntegerField: {
        'field': field.Long(signed=False),
        'query_type_list': [
            QueryTypeExact, QueryTypeGreaterThan,
            QueryTypeGreaterThanOrEqual, QueryTypeLessThan,
            QueryTypeLessThanOrEqual, QueryTypeRange, QueryTypeRangeExclusive
        ],
        'transformations': {
            'search': [ValueTransformationToInteger]
        }
    },
    models.PositiveIntegerField: {
        'field': field.Integer,
        'query_type_list': [
            QueryTypeExact, QueryTypeGreaterThan,
            QueryTypeGreaterThanOrEqual, QueryTypeLessThan,
            QueryTypeLessThanOrEqual, QueryTypeRange, QueryTypeRangeExclusive
        ],
        'transformations': {
            'search': [ValueTransformationToInteger]
        }
    },
    models.TextField: {
        'field': field.Text,
        'query_type_list': [
            QueryTypeExact, QueryTypeFuzzy, QueryTypePartial,
            QueryTypeRegularExpression, QueryTypeGreaterThan,
            QueryTypeGreaterThanOrEqual, QueryTypeLessThan,
            QueryTypeLessThanOrEqual
        ],
        'transformations': {
            'index': [
                ValueTransformationAccentReplace,
                ValueTransformationHyphenReplace, ValueTransformationCasefold
            ],
            'search': [
                ValueTransformationAccentReplace,
                ValueTransformationHyphenReplace, ValueTransformationCasefold
            ]
        }
    },
    models.UUIDField: {
        'field': field.Keyword,
        'query_type_list': [
            QueryTypeExact, QueryTypePartial, QueryTypeRegularExpression
        ],
        'transformations': {
            'index': [
                ValueTransformationToString, ValueTransformationHyphenStrip
            ],
            'search': [
                ValueTransformationToString, ValueTransformationHyphenStrip
            ]
        }
    }
}

INDEX_NAME_DELIMITER = '--'
