import whoosh
from whoosh import (
    qparser
)

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
    ValueTransformationToBoolean, ValueTransformationToDateTime,
    ValueTransformationToDateTimeSimpleFormat, ValueTransformationToInteger,
    ValueTransformationToString
)

"""
Integer field:

Whoosh:
Special field type that lets you index integer or floating point numbers
in relatively short fixed-width terms. The field converts numbers to
sortable bytes for you before indexing.

You specify the numeric type of the field (int or float) when you
create the NUMERIC object. The default is int. For int, you can specify
a size in bits (32 or 64). For both int and float you can specify a
signed keyword argument (default is True).

Positive integer field:

Django:
Like an IntegerField, but must be either positive or zero (0).
Values from 0 to 2147483647 are safe in all databases supported by
Django. The value 0 is accepted for backward compatibility reasons.
https://docs.djangoproject.com/en/3.2/ref/models/fields/#positiveintegerfield

Whoosh:
Special field type that lets you index integer or floating point numbers
in relatively short fixed-width terms. The field converts numbers to
sortable bytes for you before indexing.

You specify the numeric type of the field (int or float) when you
create the NUMERIC object. The default is int. For int, you can specify
a size in bits (32 or 64). For both int and float you can specify a
signed keyword argument (default is True).
"""

DJANGO_TO_WHOOSH_FIELD_MAP = {
    models.AutoField: {
        'field': whoosh.fields.ID(stored=True, unique=True),
        'query_type_list': [
            QueryTypeExact, QueryTypePartial, QueryTypeGreaterThan,
            QueryTypeGreaterThanOrEqual, QueryTypeLessThan,
            QueryTypeLessThanOrEqual, QueryTypeRange, QueryTypeRangeExclusive
        ],
        'transformations': {
            'index': [ValueTransformationToString]
        }
    },
    models.BigIntegerField: {
        'field': whoosh.fields.NUMERIC(bits=64),
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
        'field': whoosh.fields.BOOLEAN,
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
        'field': whoosh.fields.TEXT,
        'query_type_list': [
            QueryTypeExact, QueryTypeFuzzy, QueryTypePartial,
            QueryTypeRegularExpression, QueryTypeGreaterThan,
            QueryTypeGreaterThanOrEqual, QueryTypeLessThan,
            QueryTypeLessThanOrEqual
        ],
        'transformations': {
            'index': [
                ValueTransformationAccentReplace,
                ValueTransformationAtReplace,
                ValueTransformationHyphenReplace
            ],
            'search': [
                ValueTransformationAccentReplace,
                ValueTransformationAtReplace,
                ValueTransformationHyphenReplace
            ]
        }
    },
    models.DateTimeField: {
        'field': whoosh.fields.DATETIME,
        'query_type_list': [
            QueryTypeExact, QueryTypeGreaterThan,
            QueryTypeGreaterThanOrEqual, QueryTypeLessThan,
            QueryTypeLessThanOrEqual, QueryTypeRange, QueryTypeRangeExclusive
        ],
        'transformations': {
            'search': [
                ValueTransformationToDateTime,
                ValueTransformationToDateTimeSimpleFormat
            ]
        }
    },
    models.EmailField: {
        'field': whoosh.fields.TEXT,
        'query_type_list': [
            QueryTypeExact, QueryTypePartial
        ],
        'transformations': {
            'index': [
                ValueTransformationAtReplace, ValueTransformationCasefold
            ],
            'search': [
                ValueTransformationAtReplace, ValueTransformationCasefold
            ]
        }
    },
    models.IntegerField: {
        'field': whoosh.fields.NUMERIC,
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
        'field': whoosh.fields.NUMERIC(bits=64, signed=False),
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
        'field': whoosh.fields.NUMERIC(signed=False),
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
        'field': whoosh.fields.TEXT,
        'query_type_list': [
            QueryTypeExact, QueryTypeFuzzy, QueryTypePartial,
            QueryTypeRegularExpression, QueryTypeGreaterThan,
            QueryTypeGreaterThanOrEqual, QueryTypeLessThan,
            QueryTypeLessThanOrEqual
        ],
        'transformations': {
            'index': [
                ValueTransformationAccentReplace,
                ValueTransformationAtReplace,
                ValueTransformationHyphenReplace
            ],
            'search': [
                ValueTransformationAccentReplace,
                ValueTransformationAtReplace,
                ValueTransformationHyphenReplace
            ]
        }
    },
    models.UUIDField: {
        'field': whoosh.fields.ID(unique=True),
        'query_type_list': [
            QueryTypeExact, QueryTypePartial, QueryTypeRegularExpression
        ],
        'transformations': {
            'index': [
                ValueTransformationToString, ValueTransformationHyphenReplace
            ],
            'search': [
                ValueTransformationToString, ValueTransformationHyphenReplace
            ]
        }
    }
}

TEXT_LOCK_INSTANCE_DEINDEX = 'dynamic_search_deindex_instance'
TEXT_LOCK_INSTANCE_INDEX = 'dynamic_search_index_instance'

WHOOSH_INDEX_DIRECTORY_NAME = 'whoosh'
