from django.core import management
from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.classes import (
    InitializationStep, ManagementCommandInitializationReporter
)
from mayan.apps.app_manager.literals import PROCESS_INITIAL_SETUP


class Command(management.BaseCommand):
    help = 'Initializes an install and gets it ready to be used.'

    def add_arguments(self, parser):
        InitializationStep.do_add_arguments(
            parser=parser, process=PROCESS_INITIAL_SETUP
        )

    def handle(self, *args, **options):
        reporter = ManagementCommandInitializationReporter(
            command=self, title=_(message='Initial setup')
        )

        errors = InitializationStep.do_process(
            options=options, process=PROCESS_INITIAL_SETUP, reporter=reporter
        )

        if errors:
            exit(1)
