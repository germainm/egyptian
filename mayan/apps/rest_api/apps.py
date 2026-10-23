import re

from django.apps import apps
from django.conf import settings
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.common.menus import menu_tools
from mayan.apps.organizations.settings import (
    setting_organization_url_base_path
)

from .links import (
    link_api, link_api_documentation, link_api_documentation_redoc
)


class RESTAPIApp(MayanAppConfig):
    app_url = 'api'
    app_namespace = 'rest_api'
    has_tests = True
    name = 'mayan.apps.rest_api'
    static_media_ignore_patterns = (
        'rest_framework/docs/*', 'rest_framework/img/glyphicons*',
    )
    verbose_name = _(message='REST API')

    def ready(self):
        super().ready()
        from .urls import api_version_urls

        base_path = setting_organization_url_base_path.value
        if base_path:
            installation_base_url = '/{}'.format(
                re.escape(pattern=base_path)
            )
        else:
            installation_base_url = ''

        app_url = re.escape(pattern=self.app_url)

        settings.LOGIN_REQUIRED_EXEMPT_URLS += (
            r'^{}/{}/'.format(installation_base_url, app_url),
        )

        settings.LOGIN_REQUIRED_EXEMPT_URLS += (
            r'^{}/{}/.+$'.format(installation_base_url, app_url),
        )
        menu_tools.bind_links(
            links=(
                link_api, link_api_documentation,
                link_api_documentation_redoc
            )
        )

        for app in apps.get_app_configs():
            if getattr(app, 'has_rest_api', False):
                app_api_urls = import_string(
                    dotted_path='{}.urls.api_urls'.format(app.name)
                )
                api_version_urls.extend(app_api_urls)
