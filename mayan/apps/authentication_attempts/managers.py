from django.db import models

from axes.helpers import (
    get_client_ip_address, get_client_user_agent
)

from .events import event_user_login_failed, event_user_login_succeeded
from .literals import (
    CONFIG_OPTION_LOG_FAILURE, CONFIG_OPTION_LOG_KNOWN_USERS_ONLY,
    CONFIG_OPTION_LOG_SUCCESS, LOGIN_ATTEMPT_RESULT_FAILURE,
    LOGIN_ATTEMPT_RESULT_SUCCESS
)
from .settings import get_authentication_attempts_setting_config_value

EVENT_MAP = {
    LOGIN_ATTEMPT_RESULT_FAILURE: event_user_login_failed,
    LOGIN_ATTEMPT_RESULT_SUCCESS: event_user_login_succeeded
}


class LoginAttemptManager(models.Manager):
    def create_from_request(
        self, request, result, source, user, username
    ):
        ip_address = None
        user_agent = ''

        if request is not None:
            ip_address = get_client_ip_address(request)
            user_agent = get_client_user_agent(request) or ''

        login_attempt = self.create(
            ip_address=ip_address, result=result, source=source, user=user,
            user_agent=user_agent, username=username
        )

        EVENT_MAP[result].commit(
            action_object=user, actor=login_attempt, target=login_attempt
        )

        return login_attempt

    def process_login_attempt(self, request, result, source, username):
        if result == LOGIN_ATTEMPT_RESULT_SUCCESS:
            if not get_authentication_attempts_setting_config_value(key=CONFIG_OPTION_LOG_SUCCESS):
                return
        else:
            if not get_authentication_attempts_setting_config_value(key=CONFIG_OPTION_LOG_FAILURE):
                return

        user = self.model.get_user_for_username(username=username)

        if user is None and get_authentication_attempts_setting_config_value(key=CONFIG_OPTION_LOG_KNOWN_USERS_ONLY):
            return

        return self.create_from_request(
            request=request, result=result, source=source, user=user,
            username=username
        )
