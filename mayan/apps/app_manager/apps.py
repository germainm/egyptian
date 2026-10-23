from functools import cache
import logging
from pathlib import Path
import sys
import traceback

from django.apps import apps, AppConfig
from django.core.checks import register
from django.urls import include, re_path
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.menus import menu_tools
from mayan.apps.common.utils import get_class_full_name
from mayan.apps.forms import column_widgets
from mayan.apps.navigation.source_columns import SourceColumn
from mayan.apps.organizations.settings import (
    setting_organization_url_base_path
)
from mayan.settings import BASE_DIR

from .checks import check_initialization_step_arguments
from .links import link_app_list

logger = logging.getLogger(name=__name__)


class MayanAppConfig(AppConfig):
    app_namespace = None
    app_url = None
    has_app_translations = True
    has_rest_api = False
    has_tests = False

    @classmethod
    def get_all(cls):
        list_apps = [
            app for app in apps.get_app_configs() if issubclass(app.__class__, MayanAppConfig)
        ]

        return sorted(
            list_apps, key=lambda x: str(x.verbose_name)
        )

    @classmethod
    @cache
    def get_by_namespace(cls, namespace):
        for app_config in apps.get_app_configs():
            app_namespace = getattr(app_config, 'app_namespace', None)

            if app_namespace == namespace:
                return app_config

        raise KeyError(
            'No app found with `namespace` "{}"'.format(namespace)
        )

    def configure_urls(self):
        from mayan.urls import urlpatterns as mayan_urlpatterns

        installation_base_url = setting_organization_url_base_path.value
        if installation_base_url:
            installation_base_url = '{}/'.format(installation_base_url)
        else:
            installation_base_url = ''

        if self.app_url:
            top_url = '{installation_base_url}{app_urls}/'.format(
                app_urls=self.app_url,
                installation_base_url=installation_base_url
            )
        elif self.app_url is not None:
            top_url = installation_base_url
        else:
            top_url = '{installation_base_url}{app_name}/'.format(
                app_name=self.name,
                installation_base_url=installation_base_url
            )

        try:
            app_urlpatterns = import_string(
                dotted_path='{}.urls.urlpatterns'.format(self.name)
            )
        except ImportError as exception:
            non_critical_error_list = (
                'No module named urls',
                'No module named \'{}.urls\''.format(self.name),
                'Module "{}.urls" does not define a "urlpatterns" attribute/class'.format(self.name)
            )
            if str(exception) not in non_critical_error_list:
                logger.exception(
                    'Import time error when running AppConfig.ready() of app '
                    '"%s".', self.name
                )
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)
                raise exception
        else:
            if self.app_namespace is not None:
                app_namespace = self.app_namespace
            else:
                app_namespace = self.name

            mayan_urlpatterns += (
                re_path(
                    route=r'^{}'.format(top_url), view=include(
                        (app_urlpatterns, app_namespace)
                    )
                ),
            )

        try:
            passthru_urlpatterns = import_string(
                dotted_path='{}.urls.passthru_urlpatterns'.format(self.name)
            )
        except ImportError as exception:
            non_critical_error_list = (
                'No module named urls',
                'No module named \'{}.urls\''.format(self.name),
                'Module "{}.urls" does not define a "passthru_urlpatterns" attribute/class'.format(self.name)
            )
            if str(exception) not in non_critical_error_list:
                logger.exception(
                    'Import time error when running AppConfig.ready() of app '
                    '"%s".', self.name
                )
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)
                raise exception
        else:
            mayan_urlpatterns += (
                re_path(
                    route=r'^{}'.format(top_url), view=include(
                        passthru_urlpatterns
                    )
                ),
            )

    def get_app_class_full_path(self):
        return get_class_full_name(klass=self.__class__)

    get_app_class_full_path.short_description = _(
        message='App class full path'
    )

    def get_app_url(self):
        return self.app_url or ''

    get_app_url.short_description = _(message='App URL')

    def get_has_app_translations(self):
        return getattr(self, 'has_app_translations', True)

    def get_has_javascript_translations(self):
        return getattr(self, 'has_javascript_translations', False)

    def get_has_rest_api(self):
        return getattr(self, 'has_rest_api', False)

    get_has_rest_api.short_description = _(message='Has REST API')

    def get_has_tests(self):
        return getattr(self, 'has_tests', False)

    get_has_tests.short_description = _(message='Has tests')

    def get_name(self):
        return self.name

    get_name.short_description = _(message='Name')

    def get_verbose_name(self):
        return self.verbose_name

    get_verbose_name.short_description = _(message='Verbose name')

    @property
    def mayan_path(self):
        return Path(self.path)

    @property
    def mayan_path_relative(self):
        return self.mayan_path.relative_to(BASE_DIR.parent)

    def ready(self):
        logger.debug('Initializing app: %s', self.name)
        self.configure_urls()


class AppManagerAppConfig(MayanAppConfig):
    app_namespace = 'app_manager'
    app_url = 'app_manager'
    has_tests = True
    name = 'mayan.apps.app_manager'
    verbose_name = _(message='App manager')

    def ready(self):
        super().ready()

        SourceColumn(
            attribute='get_verbose_name', include_label=True,
            is_identifier=True, source=MayanAppConfig
        )
        SourceColumn(
            attribute='get_app_url', include_label=True,
            source=MayanAppConfig
        )
        SourceColumn(
            attribute='get_name', include_label=True,
            source=MayanAppConfig
        )
        SourceColumn(
            attribute='get_app_class_full_path', include_label=True,
            source=MayanAppConfig
        )
        SourceColumn(
            attribute='get_has_rest_api', include_label=True, source=MayanAppConfig,
            widget=column_widgets.TwoStateWidget
        )
        SourceColumn(
            attribute='get_has_tests', include_label=True, source=MayanAppConfig,
            widget=column_widgets.TwoStateWidget
        )

        menu_tools.bind_links(
            links=(link_app_list,)
        )

        register(check=check_initialization_step_arguments)
