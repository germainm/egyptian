import logging

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from django.urls import re_path
from django.utils.translation import gettext_lazy as _

import mayan
from mayan.apps.common.utils import any_to_bool
from mayan.apps.icons.icons import Icon
from mayan.apps.navigation.links import Link
from mayan.apps.platforms.classes import ClientBackend
from mayan.apps.platforms.permissions import permission_test_trigger

logger = logging.getLogger(name=__name__)


class ClientBackendSentry(ClientBackend):
    _url_namespace = 'sentry'

    def get_links(self):
        icon_sentry_debug = Icon(
            driver_name='fontawesome', symbol='bug'
        )

        return (
            Link(
                icon=icon_sentry_debug,
                permission=permission_test_trigger,
                text=_(message='Sentry test error'),
                view='platforms:sentry_debug',
            ),
        )

    def get_url_patterns(self):
        def view_trigger_error(request):
            1 / 0

        return [
            re_path(
                route=r'^debug/$', name='sentry_debug',
                view=view_trigger_error
            )
        ]

    def launch(self):
        kwargs = self.setup_arguments()

        kwargs['integrations'] = (
            CeleryIntegration(), DjangoIntegration(), RedisIntegration()
        )

        logger.debug('cleaned arguments: %s', kwargs)

        sentry_instance = sentry_sdk.init(**kwargs)

        logger.debug('client options: %s', sentry_instance._client.options)

    def get_release(self):
        return mayan.__build_revision__ or mayan.__version__

    def setup_arguments(self):
        logger.debug('raw arguments: %s', self.kwargs)

        options = {}

        options['dsn'] = self.kwargs['dsn']

        options['debug'] = any_to_bool(
            value=self.kwargs.get('debug', False)
        )

        options['release'] = self.get_release()

        options['environment'] = self.kwargs.get('environment')

        options['profiles_sample_rate'] = float(
            self.kwargs.get('profiles_sample_rate', 1.0)
        )

        options['max_breadcrumbs'] = int(
            self.kwargs.get('max_breadcrumbs', 100)
        )

        options['attach_stacktrace'] = any_to_bool(
            value=self.kwargs.get('attach_stacktrace', False)
        )

        options['send_default_pii'] = any_to_bool(
            value=self.kwargs.get('send_default_pii', True)
        )

        options['server_name'] = self.kwargs.get('server_name')

        options['include_local_variables'] = any_to_bool(
            value=self.kwargs.get('include_local_variables', True)
        )

        options['transport'] = self.kwargs.get('transport')

        options['http_proxy'] = self.kwargs.get('http_proxy')

        options['https_proxy'] = self.kwargs.get('https_proxy')

        options['shutdown_timeout'] = int(
            self.kwargs.get('shutdown_timeout', 2)
        )

        options['traces_sample_rate'] = float(
            self.kwargs.get('traces_sample_rate', 0.005)
        )

        return options
