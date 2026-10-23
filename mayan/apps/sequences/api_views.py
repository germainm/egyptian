from mayan.apps.rest_api import generics

from .exceptions import SequenceExhausted, SequenceExhaustedAPIError
from .models import Sequence
from .permissions import (
    permission_sequence_create, permission_sequence_delete,
    permission_sequence_edit, permission_sequence_use,
    permission_sequence_view
)
from .serializers import SequenceSerializer, SequenceValueNextSerializer


class APISequenceListView(generics.ListCreateAPIView):
    """
    get: Returns a list of all the sequences.
    post: Create a new sequence.
    """
    mayan_object_permission_map = {'GET': permission_sequence_view}
    mayan_view_permission_map = {'POST': permission_sequence_create}
    serializer_class = SequenceSerializer
    source_queryset = Sequence.objects.all()

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class APISequenceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    delete: Delete the selected sequence.
    get: Return the details of the selected sequence.
    patch: Edit the selected sequence.
    put: Edit the selected sequence.
    """
    lookup_url_kwarg = 'sequence_id'
    mayan_object_permission_map = {
        'DELETE': permission_sequence_delete,
        'GET': permission_sequence_view,
        'PATCH': permission_sequence_edit,
        'PUT': permission_sequence_edit
    }
    serializer_class = SequenceSerializer
    source_queryset = Sequence.objects.all()

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class APISequenceValueNextView(generics.ObjectActionAPIView):
    """
    post: Consume and return the next value or values of the sequence.
    """
    lookup_url_kwarg = 'sequence_id'
    mayan_object_permission_map = {'POST': permission_sequence_use}
    serializer_class = SequenceValueNextSerializer
    source_queryset = Sequence.objects.all()

    def object_action(self, obj, request, serializer):
        count = serializer.validated_data['count']

        try:
            value_list = obj.do_value_list_next(
                count=count, user=request.user
            )
        except SequenceExhausted as exception:
            raise SequenceExhaustedAPIError(
                detail=str(exception)
            )

        return {'value_list': value_list}
