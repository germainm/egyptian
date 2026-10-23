from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Value
from django.db.models.functions import Cast, Replace
from django.utils.translation import gettext_lazy as _

from ...exceptions import DynamicSearchValueTransformationError
from ...search_backends import SearchBackend
from ...search_fields import SearchFieldVirtualAllFields
from ...search_models import SearchModel

from .literals import DJANGO_TO_DJANGO_FIELD_MAP


class DjangoSearchBackend(SearchBackend):
    label = _(message='Django ORM')
    field_type_mapping = DJANGO_TO_DJANGO_FIELD_MAP

    def _do_search_model_filter(self, filter_kwargs, search_field):
        if search_field.field_class == models.UUIDField:
            replace_function = Replace(
                expression=Cast(
                    expression=search_field.field_name,
                    output_field=models.CharField()
                ), text=Value('-'), replacement=Value(''),
                output_field=models.CharField()
            )
        else:
            replace_function = Replace(
                expression=Cast(
                    expression=search_field.field_name,
                    output_field=models.CharField()
                ), text=Value('-'), replacement=Value('_'),
                output_field=models.CharField()
            )

        queryset = search_field.search_model.get_queryset().annotate(
            **{
                '{}_clean'.format(search_field.field_name): replace_function
            }
        )

        try:
            queryset = queryset.filter(filter_kwargs)
            values = queryset.values_list('pk', flat=True)

            values_unique = tuple(
                set(values)
            )

            for entry in values_unique:
                yield entry
        except ValidationError:
            return ()

    def _get_status(self):
        result = []

        for search_model in SearchModel.all():
            queryset = search_model.get_queryset()
            object_count = queryset.count()

            result.append(
                {'search_model': search_model, 'object_count': object_count}
            )

        return result

    def _search(
        self, search_field, query_type, value, is_quoted_value=False,
        is_raw_value=False
    ):
        self.do_query_type_verify(
            query_type=query_type, search_field=search_field
        )

        if isinstance(search_field, SearchFieldVirtualAllFields):
            result = set()

            for search_field in search_field.field_composition:
                try:
                    search_field_query = query_type.resolve_for_backend(
                        is_quoted_value=is_quoted_value,
                        is_raw_value=is_raw_value, search_backend=self,
                        search_field=search_field, value=value
                    )
                except DynamicSearchValueTransformationError:
                    """Skip the search field."""
                else:
                    if search_field_query is not None:
                        field_id_list = self._do_search_model_filter(
                            filter_kwargs=search_field_query,
                            search_field=search_field
                        )

                        result.update(field_id_list)

            return result
        else:
            try:
                filter_kwargs = query_type.resolve_for_backend(
                    is_quoted_value=is_quoted_value,
                    is_raw_value=is_raw_value, search_backend=self,
                    search_field=search_field, value=value
                )
            except DynamicSearchValueTransformationError:
                return ()
            else:
                if filter_kwargs is None:
                    return ()
                else:
                    return self._do_search_model_filter(
                        filter_kwargs=filter_kwargs, search_field=search_field
                    )
