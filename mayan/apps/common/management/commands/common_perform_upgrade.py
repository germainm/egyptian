from django.core import management
from django.utils.translation import gettext_lazy as _

from mayan.apps.app_manager.classes import (
    InitializationStep, ManagementCommandInitializationReporter
)
from mayan.apps.app_manager.literals import PROCESS_UPGRADE


class Command(management.BaseCommand):
    help = 'Performs the required steps after a version upgrade.'

    def add_arguments(self, parser):
        InitializationStep.do_add_arguments(
            parser=parser, process=PROCESS_UPGRADE
        )

    def handle(self, *args, **options):
        reporter = ManagementCommandInitializationReporter(
            command=self, title=_(message='Upgrade')
        )

        errors = InitializationStep.do_process(
            options=options, process=PROCESS_UPGRADE, reporter=reporter
        )

        if errors:
            exit(1)
