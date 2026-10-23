from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig

from .template_backends import TemplateContextEntry


class TemplatingApp(MayanAppConfig):
    app_namespace = 'templating'
    app_url = 'templating'
    has_javascript_translations = True
    has_rest_api = True
    has_static_media = True
    has_tests = True
    name = 'mayan.apps.templating'
    verbose_name = _(message='Templating')

    def ready(self):
        super().ready()

        TemplateContextEntry(
            always_available=True,
            description=_(message='Current date and time'), name='now',
            value=timezone.now
        )
