from rest_framework.exceptions import ParseError

from mayan.apps.rest_api import generics

from ..exceptions import (
    DynamicSearchAPIErrorServiceUnavailable,
    DynamicSearchBackendResourceError, DynamicSearchException
)
from ..search_models import SearchModel
from ..serializers import (
    DummySearchResultModelSerializer, SearchModelSerializer
)
from ..views.view_mixins import SearchResultViewMixin

from .api_view_mixins import SearchModelAPIViewMixin


class APISearchModelDetailView(
    SearchModelAPIViewMixin, generics.RetrieveAPIView
):
    """
    get: Returns the details of the selected search models.
    """

    serializer_class = SearchModelSerializer

    def get_object(self):
        return self.get_search_model()


class APISearchModelList(generics.ListAPIView):
    """
    get: Returns a list of all the available search models.
    """

    serializer_class = SearchModelSerializer

    def get_source_queryset(self):
        return SearchModel.all()


class APISearchView(
    SearchResultViewMixin, SearchModelAPIViewMixin, generics.ListAPIView
):
    """
    get: Perform a search operation.
    """

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return DummySearchResultModelSerializer
        else:
            return self.search_model.serializer

    def get_source_queryset(self):
        try:
            return self.get_search_queryset()
        except DynamicSearchBackendResourceError as exception:
            raise DynamicSearchAPIErrorServiceUnavailable(
                detail=str(exception)
            )
        except DynamicSearchException as exception:
            raise ParseError(
                detail=str(exception)
            )
