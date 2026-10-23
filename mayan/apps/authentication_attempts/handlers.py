from django.apps import apps

from .literals import (
    LOGIN_ATTEMPT_RESULT_FAILURE, LOGIN_ATTEMPT_RESULT_SUCCESS,
    LOGIN_ATTEMPT_SOURCE_SESSION
)


def handler_user_logged_in(sender, user, request=None, **kwargs):
    LoginAttempt = apps.get_model(
        app_label='authentication_attempts', model_name='LoginAttempt'
    )

    LoginAttempt.objects.process_login_attempt(
        request=request, result=LOGIN_ATTEMPT_RESULT_SUCCESS,
        source=LOGIN_ATTEMPT_SOURCE_SESSION,
        username=user.get_username()
    )


def handler_user_login_failed(
    sender, credentials=None, request=None, **kwargs
):
    LoginAttempt = apps.get_model(
        app_label='authentication_attempts', model_name='LoginAttempt'
    )

    credentials = credentials or {}

    username = credentials.get('username', None) or ''

    LoginAttempt.objects.process_login_attempt(
        request=request, result=LOGIN_ATTEMPT_RESULT_FAILURE,
        source=LOGIN_ATTEMPT_SOURCE_SESSION,
        username=username
    )
