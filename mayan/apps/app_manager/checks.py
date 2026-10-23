from django.core.checks import Error

from .classes import (
    InitializationStep, PROCESS_INITIAL_SETUP, PROCESS_UPGRADE
)
from .exceptions import InitializationStepError


def check_initialization_step_arguments(app_configs, **kwargs):
    errors = []

    for process in (PROCESS_INITIAL_SETUP, PROCESS_UPGRADE):
        try:
            InitializationStep.get_arguments(process=process)
        except InitializationStepError as exception:
            errors.append(
                Error(
                    str(exception), id='app_manager.E001',
                    obj='InitializationStep'
                )
            )

    return errors
