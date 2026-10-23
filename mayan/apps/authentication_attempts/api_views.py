from django.contrib.auth import get_user_model

from mayan.apps.rest_api import generics
from mayan.apps.rest_api.api_view_mixins import ExternalObjectAPIViewMixin

from .models import LoginAttempt
from .permissions import permission_login_attempt_view
from .serializers import LoginAttemptSerializer


class APILoginAttemptListView(generics.ListAPIView):
    """
    get: Return a list of the login attempts of all users.
    """
    mayan_object_permission_map = {'GET': permission_login_attempt_view}
    serializer_class = LoginAttemptSerializer
    source_queryset = LoginAttempt.objects.all()


class APILoginAttemptDetailView(generics.RetrieveAPIView):
    """
    get: Return the details of the selected login attempt.
    """
    lookup_url_kwarg = 'login_attempt_id'
    mayan_object_permission_map = {'GET': permission_login_attempt_view}
    serializer_class = LoginAttemptSerializer
    source_queryset = LoginAttempt.objects.all()


class APICurrentUserLoginAttemptListView(generics.ListAPIView):
    """
    get: Return a list of the login attempts of the current user.
    """
    serializer_class = LoginAttemptSerializer

    def get_source_queryset(self):
        if self.request.user.is_authenticated:
            return self.request.user.login_attempts.all()
        else:
            return LoginAttempt.objects.none()


class APIUserLoginAttemptListView(
    ExternalObjectAPIViewMixin, generics.ListAPIView
):
    """
    get: Return a list of the login attempts of the selected user.
    """
    external_object_class = get_user_model()
    external_object_pk_url_kwarg = 'user_id'
    mayan_external_object_permission_map = {
        'GET': permission_login_attempt_view
    }
    serializer_class = LoginAttemptSerializer

    def get_source_queryset(self):
        external_object = self.get_external_object()
        return external_object.login_attempts.all()
