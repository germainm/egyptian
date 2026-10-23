from django.urls import include, re_path

from mayan.apps.backends.classes import BaseBackend
from mayan.apps.common.menus import menu_tools

from .settings import (
    setting_client_backend_arguments, setting_client_backend_enabled
)
from .urls import urlpatterns


class ClientBackend(BaseBackend):
    _loader_module_name = 'client_backends'

    @classmethod
    def get_backend_instance(cls, name):
        backend_class = cls.get(name=name)
        kwargs = setting_client_backend_arguments.value.get(
            name, {}
        )
        return backend_class(**kwargs)

    @classmethod
    def post_load_modules(cls):
        cls.register_url_patterns()
        cls.register_links()
        cls.launch_backends()

    @classmethod
    def launch_backends(cls):
        for backend_name in setting_client_backend_enabled.value:
            cls.get_backend_instance(name=backend_name).launch()

    @classmethod
    def register_links(cls):
        for backend_name in setting_client_backend_enabled.value:
            backend_instance = cls.get_backend_instance(name=backend_name)
            menu_tools.bind_links(
                links=backend_instance.get_links()
            )

    @classmethod
    def register_url_patterns(cls):
        for backend_name in setting_client_backend_enabled.value:
            backend_instance = cls.get_backend_instance(name=backend_name)

            top_url = '{}/'.format(
                getattr(
                    backend_instance, '_url_namespace',
                    backend_instance.__class__.__name__
                )
            )

            urlpatterns.append(
                re_path(
                    route=r'^{}'.format(top_url), view=include(
                        backend_instance.get_url_patterns()
                    )
                )
            )

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def get_links(self):
        return ()
