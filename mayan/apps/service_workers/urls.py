from django.urls import re_path

from .literals import (
    URL_REGULAR_SERVICE_WORKER_GATEWAY_ERROR,
    URL_REGULAR_SERVICE_WORKER_SCRIPT
)
from .views import (
    ServiceWorkerGatewayErrorView, ServiceWorkerScriptView
)

urlpatterns = [
    re_path(
        route=URL_REGULAR_SERVICE_WORKER_SCRIPT,
        name='service_worker_script',
        view=ServiceWorkerScriptView.as_view()
    ),
    re_path(
        route=URL_REGULAR_SERVICE_WORKER_GATEWAY_ERROR,
        name='service_worker_gateway_error',
        view=ServiceWorkerGatewayErrorView.as_view()
    )
]
