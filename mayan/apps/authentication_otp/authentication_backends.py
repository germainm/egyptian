from mayan.apps.authentication.authentication_backends import (
    AuthenticationBackendModelEmailPassword,
    AuthenticationBackendModelUsernamePassword
)
from mayan.apps.common.utils import get_class_full_name

from .django_authentication_backends import (
    DjangoAuthenticationBackendEmailMultiFactorOTP,
    DjangoAuthenticationBackendUsernameMultiFactorOTP
)
from .forms import AuthenticationFormTOTP


class AuthenticationBackendTOTPMixin:
    def __init__(self, **kwargs):
        self.form_list += (AuthenticationFormTOTP,)

        super().__init__(**kwargs)


class AuthenticationBackendModelEmailPasswordTOTP(
    AuthenticationBackendTOTPMixin, AuthenticationBackendModelEmailPassword
):

    django_authentication_backend_paths = (
        get_class_full_name(klass=DjangoAuthenticationBackendEmailMultiFactorOTP),
    )


class AuthenticationBackendModelUsernamePasswordTOTP(
    AuthenticationBackendTOTPMixin,
    AuthenticationBackendModelUsernamePassword
):

    django_authentication_backend_paths = (
        get_class_full_name(klass=DjangoAuthenticationBackendUsernameMultiFactorOTP),
    )
