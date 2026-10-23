import inspect

from django.conf import settings
from django.contrib.auth import _clean_credentials
from django.contrib.auth.signals import user_login_failed
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.utils.module_loading import import_string

from mayan.apps.backends.classes import BaseBackend

from .literals import AXES_BACKEND_DOTTED_PATH
from .settings import (
    setting_authentication_backend, setting_authentication_backend_arguments
)


class AuthenticationBackend(BaseBackend):
    AUTHENTICATION_BACKENDS_ORIGINAL = None
    _loader_module_name = 'authentication_backends'
    django_authentication_backend_paths = ()
    form_list = ()
    login_form_class = None
    login_form_class_path = 'django.contrib.auth.forms.AuthenticationForm'

    @classmethod
    def cls_get_instance(cls):
        authentication_backend_class = cls.get(
            name=setting_authentication_backend.value
        )
        return authentication_backend_class(
            **setting_authentication_backend_arguments.value
        )

    @classmethod
    def cls_initialize(cls):
        from .forms import AuthenticationForm

        cls.AUTHENTICATION_BACKENDS_ORIGINAL = settings.AUTHENTICATION_BACKENDS

        backend = cls.cls_get_instance()
        backend.do_initialize()

        login_form_class = backend.get_login_form_class()

        if issubclass(login_form_class, AuthenticationForm):
            if AXES_BACKEND_DOTTED_PATH not in settings.AUTHENTICATION_BACKENDS:
                settings.AUTHENTICATION_BACKENDS = (AXES_BACKEND_DOTTED_PATH,) + tuple(
                    settings.AUTHENTICATION_BACKENDS
                )

    @classmethod
    def cls_deinitialize(cls):
        backend = cls.cls_get_instance()
        backend.do_deinitialize()

    def do_deinitialize(self):
        settings.AUTHENTICATION_BACKENDS = self.__class__.AUTHENTICATION_BACKENDS_ORIGINAL

    def do_initialize(self):
        if self.django_authentication_backend_paths:
            settings.AUTHENTICATION_BACKENDS = self.django_authentication_backend_paths

    def do_process(self, request, form_list=None, kwargs=None):
        pass

    def get_django_authentication_backends(self, request, **credentials):
        from .forms import AuthenticationForm

        if issubclass(self.get_login_form_class(), AuthenticationForm):
            django_authentication_backend_path_list = [AXES_BACKEND_DOTTED_PATH]
        else:
            django_authentication_backend_path_list = []

        reported_django_authentication_backend_path_list = self.get_django_authentication_backend_paths()
        django_authentication_backend_path_list.extend(reported_django_authentication_backend_path_list)

        for path in django_authentication_backend_path_list:
            try:
                backend_class = import_string(dotted_path=path)
            except ImportError as exception:
                raise ImproperlyConfigured(
                    'Unable to import Django authentication backend from '
                    'the provided dotted path.'
                ) from exception
            else:
                backend = backend_class()
                backend_signature = inspect.signature(obj=backend.authenticate)
                try:
                    backend_signature.bind(request, **credentials)
                except TypeError:
                    continue
                else:
                    yield backend, path

    def authenticate(self, request, **credentials):
        django_authentication_backend_list = self.get_django_authentication_backends(
            credentials=credentials, request=request
        )
        for backend, backend_path in django_authentication_backend_list:
            try:
                user = backend.authenticate(request=request, **credentials)
            except PermissionDenied:
                break
            else:
                if user is not None:
                    user.backend = backend_path
                    return user

        credentials_masked = _clean_credentials(credentials=credentials)

        user_login_failed.send(
            credentials=credentials_masked, request=request,
            sender=type(self).__module__
        )

    def get_condition_dict(self):
        result = {}

        for form_index, form in enumerate(iterable=self.form_list):
            condition = getattr(form, 'condition', None)
            if condition:
                def condition_wrapper(authentication_backend):
                    def wrapper(wizard):
                        return condition(
                            authentication_backend=authentication_backend,
                            wizard=wizard
                        )

                    return wrapper

                condition_result = condition_wrapper(
                    authentication_backend=self
                )
                result[
                    str(form_index)
                ] = condition_result

        return result

    def get_context_data(self):
        return {}

    def get_django_authentication_backend_paths(self):
        return self.django_authentication_backend_paths

    def get_form_list(self):
        return self.form_list

    def get_login_form_class(self):
        if not self.login_form_class:
            if not self.login_form_class_path:
                raise ImproperlyConfigured(
                    'Must specify a `login_form_class` or a '
                    '`login_form_class_path`.'
                )
            else:
                return import_string(
                    dotted_path=self.login_form_class_path
                )
        else:
            return self.login_form_class

    def get_user(self, request, form_list=None, kwargs=None):
        raise NotImplementedError


class AuthenticationBackendRememberMeMixin:
    def __init__(self, **kwargs):
        self.maximum_session_length = kwargs.pop('maximum_session_length')
        super().__init__(**kwargs)

    def do_process(self, form_list=None, kwargs=None, request=None):
        super().do_process(
            form_list=form_list, kwargs=kwargs, request=request
        )
        kwargs = kwargs or {}
        remember_me = kwargs.get('remember_me')


        if remember_me is True:
            request.session.set_expiry(
                self.maximum_session_length
            )
        elif remember_me is False:
            request.session.set_expiry(0)
