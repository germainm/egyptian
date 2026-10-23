import logging

from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig

from .patches import patch_HttpRequest
from .utils import do_asset_urls_apply_base_path

logger = logging.getLogger(name=__name__)


class OrganizationsApp(MayanAppConfig):
    app_namespace = 'organizations'
    app_url = 'organizations'
    has_tests = True
    name = 'mayan.apps.organizations'
    verbose_name = _(message='Organizations')

    def ready(self):
        super().ready()

        patch_HttpRequest()

        do_asset_urls_apply_base_path()
