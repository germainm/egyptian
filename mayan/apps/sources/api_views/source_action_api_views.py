from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from mayan.apps.acls.models import AccessControlList
from mayan.apps.rest_api import generics

from ..api_view_mixins import ParentObjectSourceAPIViewMixin
from ..exceptions import SourceActionException
from ..permissions import permission_sources_view
from ..serializers import SourceBackendActionSerializer


class APISourceActionDetailView(
    ParentObjectSourceAPIViewMixin, generics.RetrieveAPIView
):
    """
    get: Source action detail view.
    """
    lookup_url_kwarg = 'action_name'
    mayan_external_object_permission_map = {'GET': permission_sources_view}
    serializer_class = SourceBackendActionSerializer

    def get_object(self):
        for entry in self.get_queryset():
            if entry.name == self.kwargs['action_name']:
                return entry

    def get_source_queryset(self):
        return self.get_source().get_action_list()


class APISourceActionExecuteView(
    ParentObjectSourceAPIViewMixin, generics.ObjectActionAPIView
):
    """
    get: Execute a source action without confirmation.
    post: Execute a source action with confirmation.
    """
    lookup_url_kwarg = 'action_name'
    serializer_class = SourceBackendActionSerializer

    def get(self, request, *args, **kwargs):
        if self.get_object().confirmation:
            handler = self.http_method_not_allowed
            response = handler(request, *args, **kwargs)
            self.response = self.finalize_response(
                request, response, *args, **kwargs
            )
            return self.response
        else:
            return self.view_action(request, *args, **kwargs)

    def get_object(self):
        source = self.get_source()

        action = source.get_action(
            name=self.kwargs['action_name']
        )

        action_permission = action.permission


        if action_permission:
            source_queryset = self.get_parent_queryset_source()

            queryset = AccessControlList.objects.restrict_queryset(
                permission=action_permission, queryset=source_queryset,
                user=self.request.user
            )

            get_object_or_404(
                queryset=queryset, pk=self.kwargs['source_id']
            )

        return action

    def get_parent_queryset_source(self):
        return super().get_parent_queryset_source().filter(enabled=True)

    def get_serializer_extra_context(self):
        return {
            'action': self.get_object()
        }

    def get_source_queryset(self):
        source = self.get_source()

        return source.get_action_list()

    def post(self, request, *args, **kwargs):
        if self.get_object().confirmation:
            return self.view_action(request, *args, **kwargs)
        else:
            handler = self.http_method_not_allowed
            response = handler(request, *args, **kwargs)
            self.response = self.finalize_response(
                request, response, *args, **kwargs
            )
            return self.response

    def view_action(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = self.get_object()

        interface_kwargs = {}

        serializer_arguments = serializer.validated_data.get(
            'arguments', {}
        )

        interface_kwargs.update(**request.GET)
        interface_kwargs.update(**serializer_arguments)

        if action.accept_files:
            interface_kwargs['file'] = serializer.validated_data.get('file')

        interface_kwargs['request'] = request

        try:
            result = action.execute(
                interface_name='RESTAPI',
                interface_load_kwargs=interface_kwargs,
                interface_retrieve_kwargs={'view': self}
            )
        except SourceActionException as exception:
            return Response(
                data=str(exception), exception=exception,
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            return result


class APISourceActionListView(
    ParentObjectSourceAPIViewMixin, generics.ListAPIView
):
    """
    get: Source action list view.
    """
    mayan_external_object_permission_map = {'GET': permission_sources_view}
    serializer_class = SourceBackendActionSerializer

    def get_source_queryset(self):
        return list(
            self.get_source().get_action_list()
        )
