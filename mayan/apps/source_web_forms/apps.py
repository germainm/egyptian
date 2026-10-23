from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.app_manager.classes import InitializationStep
from mayan.apps.app_manager.literals import PROCESS_INITIAL_SETUP
from mayan.apps.app_manager.runlevels import runlevel_bootstrap


class SourceWebFormsApp(MayanAppConfig):
    app_namespace = 'source_web_forms'
    app_url = 'source_web_forms'
    has_tests = True
    name = 'mayan.apps.source_web_forms'
    verbose_name = _(message='Web form sources')

    def ready(self):
        super().ready()

        from .initializers import initializer_create_default_document_source

        InitializationStep(
            function=initializer_create_default_document_source,
            label=_(message='Create the default document source'),
            name='source_web_forms.create_default_document_source',
            order=10, process=PROCESS_INITIAL_SETUP,
            runlevel=runlevel_bootstrap
        )
