from django.apps import apps

from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .literals import (
    LOGIN_ATTEMPT_RESULT_FAILURE, LOGIN_ATTEMPT_SOURCE_API
)


class LoginAttemptTokenAuthentication(TokenAuthentication):
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except AuthenticationFailed:
            LoginAttempt = apps.get_model(
                app_label='authentication_attempts', model_name='LoginAttempt'
            )

            LoginAttempt.objects.process_login_attempt(
                request=request, result=LOGIN_ATTEMPT_RESULT_FAILURE,
                source=LOGIN_ATTEMPT_SOURCE_API, username=''
            )
            raise
