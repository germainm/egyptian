from importlib import import_module
import logging

from django.apps import apps

logger = logging.getLogger(name=__name__)


class AppsModuleLoaderMixin:
    __loader_class_list = []

    __loader_module_sets = {}

    _loader_module_name = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if cls.__dict__.get('_loader_module_name'):
            AppsModuleLoaderMixin.__loader_class_list.append(cls)

    @classmethod
    def get_loader_app_configs(cls):
        return apps.get_app_configs()

    @classmethod
    def get_loader_class_list(cls):
        return list(AppsModuleLoaderMixin.__loader_class_list)

    @classmethod
    def get_loader_app_configs_test(cls):
        return [
            app for app in apps.get_app_configs()
            if app.name.startswith('mayan.apps.')
        ]

    @classmethod
    def load_modules(
        cls, app_config_list=None, do_post_load=True, loader_module_name=None
    ):
        loader_module_name = loader_module_name or cls._loader_module_name

        if app_config_list is None:
            app_config_list = cls.get_loader_app_configs()

        cls.__loader_module_sets.setdefault(
            loader_module_name, set()
        )

        for app in app_config_list:
            if app not in cls.__loader_module_sets[loader_module_name]:
                try:
                    import_module(
                        name='{}.{}'.format(
                            app.name, loader_module_name
                        )
                    )
                except ImportError as exception:
                    full_module_name = '{}.{}'.format(
                        app.name, loader_module_name
                    )
                    missing_module_name = getattr(exception, 'name', None)
                    missing_module_name_string = '{}.'.format(missing_module_name)

                    app_lacks_module = False
                    if isinstance(exception, ModuleNotFoundError) and missing_module_name:
                        app_lacks_module = (
                            full_module_name == missing_module_name
                        ) or full_module_name.startswith(missing_module_name_string)

                    if not app_lacks_module:
                        raise

                finally:
                    cls.__loader_module_sets[
                        loader_module_name
                    ].add(app)

        if do_post_load:
            cls.post_load_modules()

    @classmethod
    def load_modules_test(cls):
        loader_module_name = cls._loader_module_name

        if not loader_module_name or loader_module_name.startswith('tests.'):
            return

        cls.load_modules(
            app_config_list=cls.get_loader_app_configs_test(),
            do_post_load=False, loader_module_name='tests.{}'.format(
                loader_module_name
            )
        )

    @classmethod
    def load_modules_test_all(cls):
        for loader_class in cls.get_loader_class_list():
            loader_class.load_modules_test()

    @classmethod
    def post_load_modules(cls):
        pass
