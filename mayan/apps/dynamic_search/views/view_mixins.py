from django.conf import settings
from django.contrib import messages
from django.http import Http404

from mayan.apps.views.utils import get_request_data

from ..exceptions import (
    DynamicSearchException, DynamicSearchInterpreterUnknownSearchType
)
from ..literals import FILTER_PREFIX, SEARCH_MODEL_NAME_KWARG
from ..mixins import QuerysetSearchModelMixin
from ..search_backends import SearchBackend
from ..search_interpreters import SearchInterpreter
from ..search_models import SearchModel


class SearchQueryViewMixin:
    def get_search_query(self, request=None):
        request = request or self.request

        return get_request_data(request=request)


class QuerysetSearchFilterMixin(SearchQueryViewMixin):
    def get_filtered_queryset(self, request, queryset, view):
        if not getattr(view, 'search_disable_list_filtering', False):
            search_model = self.get_search_model_from_queryset(
                queryset=queryset
            )

            if search_model:
                query_dict = self.get_search_query(request=request)

                try:
                    self.search_interpreter_filter = SearchInterpreter.init(
                        prefix=FILTER_PREFIX, query=query_dict,
                        search_model=search_model
                    )
                except DynamicSearchInterpreterUnknownSearchType:
                    return queryset
                else:
                    filter_query_clean = self.search_interpreter_filter.do_query_cleanup()

                    filter_query_is_empty = self.search_interpreter_filter.is_empty

                    if filter_query_clean and not filter_query_is_empty:
                        search_backend = SearchBackend.get_instance()
                        saved_resultset, filter_queryset = search_backend.search(
                            search_model=search_model,
                            query=filter_query_clean, queryset=queryset,
                            user=request.user
                        )

                        return filter_queryset
                    else:
                        return queryset
            else:
                return queryset
        else:
            return queryset


class SearchFilterEnabledListViewMixin(
    QuerysetSearchFilterMixin, QuerysetSearchModelMixin, SearchQueryViewMixin
):
    search_disable_list_filtering = False

    def get_context_data(self):
        context = super().get_context_data()

        context['search_disable_list_filtering'] = self.search_disable_list_filtering

        if not self.search_disable_list_filtering:
            queryset = super().get_queryset()

            search_model = self.get_search_model_from_queryset(queryset=queryset)
            if search_model:
                context.update(
                    {'search_model': search_model}
                )

                query_dict = self.get_search_query()

                try:
                    self.search_interpreter_filter = SearchInterpreter.init(
                        prefix=FILTER_PREFIX, query=query_dict,
                        search_model=search_model
                    )
                except DynamicSearchInterpreterUnknownSearchType:
                    """Ignore."""
                else:
                    query_clean = self.search_interpreter_filter.do_query_cleanup()

                    if query_clean:
                        context.update(
                            {'filter_query': query_clean}
                        )

        return context

    def get_queryset(self):
        queryset = super().get_queryset()

        try:
            return self.get_filtered_queryset(
                queryset=queryset, request=self.request, view=self
            )
        except DynamicSearchException as exception:
            if settings.DEBUG or settings.TESTING:
                raise

            messages.error(message=exception, request=self.request)

            search_model = self.get_search_model_from_queryset(
                queryset=queryset
            )
            return search_model.get_queryset().none()


class SearchModelViewMixin:
    def dispatch(self, request, *args, **kwargs):
        self.search_model = self.get_search_model()
        return super().dispatch(request=request, *args, **kwargs)

    def get_search_model_name(self):
        search_model_name = self.kwargs.get(
            SEARCH_MODEL_NAME_KWARG, self.request.GET.get(
                '_{}'.format(SEARCH_MODEL_NAME_KWARG), self.request.POST.get(
                    '_{}'.format(SEARCH_MODEL_NAME_KWARG)
                )
            )
        )

        if search_model_name:
            search_model_name = search_model_name.lower()

        return search_model_name

    def get_search_model(self):
        try:
            return SearchModel.get(
                name=self.get_search_model_name()
            )
        except KeyError as exception:
            raise Http404(
                str(exception)
            )


class SearchResultViewMixin(SearchQueryViewMixin):
    def do_search_execute(self, store_resultset=False):
        query_dict = self.get_search_query()

        self.search_interpreter = SearchInterpreter.init(
            query=query_dict, search_model=self.search_model
        )

        query_clean = self.search_interpreter.do_query_cleanup()
        query_is_empty = self.search_interpreter.is_empty

        if query_clean and not query_is_empty:
            try:
                search_backend = SearchBackend.get_instance()
                saved_resultset, queryset = search_backend.search(
                    search_model=self.search_model,
                    store_resultset=store_resultset, query=query_clean,
                    user=self.request.user
                )
            except DynamicSearchException as exception:
                if settings.DEBUG or settings.TESTING:
                    raise

                messages.error(message=exception, request=self.request)
                queryset = self.search_model.get_queryset().none()
                return (None, queryset)
            else:
                return (saved_resultset, queryset)
        else:
            queryset = self.search_model.get_queryset().none()
            return (None, queryset)

    def get_search_queryset(self):
        saved_resultset, queryset = self.do_search_execute()

        return queryset
