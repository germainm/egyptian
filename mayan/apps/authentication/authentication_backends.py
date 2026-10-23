from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from mayan.apps.common.utils import get_class_full_name

from .classes import (
    AuthenticationBackend, AuthenticationBackendRememberMeMixin
)
from .django_authentication_backends import (
    DjangoAuthenticationBackendModelEmail
)
from .forms import (
    AuthenticationFormEmailPassword, AuthenticationFormUsernamePassword
)
from .literals import SESSION_MULTI_FACTOR_USER_ID_KEY


class AuthenticationBackendModelDjangoDefault(
    AuthenticationBackendRememberMeMixin, AuthenticationBackend
):
    django_authentication_backend_paths = (
        get_class_full_name(klass=ModelBackend),
    )


class AuthenticationBackendModelUsernamePassword(
    AuthenticationBackendRememberMeMixin, AuthenticationBackend
):
    django_authentication_backend_paths = (
        get_class_full_name(klass=ModelBackend),
    )
    login_form_class = AuthenticationFormUsernamePassword

    def get_user(self, request, form_list=None, kwargs=None):
        return get_user_model().objects.get(
            pk=request.session[SESSION_MULTI_FACTOR_USER_ID_KEY]
        )


class AuthenticationBackendModelEmailPassword(
    AuthenticationBackendRememberMeMixin, AuthenticationBackend
):
    django_authentication_backend_paths = (
        get_class_full_name(klass=DjangoAuthenticationBackendModelEmail),
    )
    login_form_class = AuthenticationFormEmailPassword

    def get_user(self, request, form_list=None, kwargs=None):
        return get_user_model().objects.get(
            pk=request.session[SESSION_MULTI_FACTOR_USER_ID_KEY]
        )
