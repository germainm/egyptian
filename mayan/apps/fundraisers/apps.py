from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig


class FundraisersAppConfig(MayanAppConfig):
    app_namespace = 'fundraisers'
    app_url = 'fundraisers'
    has_static_media = True
    has_tests = True
    name = 'mayan.apps.fundraisers'
    verbose_name = _(message='Fundraisers')
