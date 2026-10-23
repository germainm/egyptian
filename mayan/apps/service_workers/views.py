import json

from django.contrib.auth.decorators import login_not_required
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

import mayan

from .settings import (
    setting_cache_refresh_interval, setting_enabled, setting_retry_interval
)
from .view_mixins import ViewMixinServiceWorkerStylesheet


@method_decorator(login_not_required, name='dispatch')
class ServiceWorkerGatewayErrorView(
    ViewMixinServiceWorkerStylesheet, TemplateView
):
    content_type = 'text/html; charset=utf-8'
    http_method_names = ('get',)
    template_name = 'service_workers/gateway_error.html'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['X-Robots-Tag'] = 'noindex, nofollow'

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'retry_interval': setting_retry_interval.value,
                'stylesheet_url_list': self.get_stylesheet_url_list()
            }
        )

        return context


@method_decorator(login_not_required, name='dispatch')
class ServiceWorkerScriptView(
    ViewMixinServiceWorkerStylesheet, TemplateView
):
    content_type = 'application/javascript; charset=utf-8'
    http_method_names = ('get',)
    template_name = 'service_workers/service_worker_script.js'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        stylesheet_url_list = self.get_stylesheet_url_list()

        error_page_html = render_to_string(
            context={
                'retry_interval': setting_retry_interval.value,
                'stylesheet_url_list': stylesheet_url_list
            },
            request=self.request,
            template_name='service_workers/gateway_error.html'
        )

        context.update(
            {
                'asset_url_json': json.dumps(obj=stylesheet_url_list),
                'cache_refresh_interval': setting_cache_refresh_interval.value,
                'enabled': setting_enabled.value,
                'error_page_json': json.dumps(obj=error_page_html),
                'error_page_url': reverse(
                    viewname='service_workers:service_worker_gateway_error'
                ),
                'version': mayan.__version__
            }
        )

        return context
