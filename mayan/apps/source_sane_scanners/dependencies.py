from django.utils.translation import gettext_lazy as _

from mayan.apps.dependencies.classes import BinaryDependency
from mayan.apps.dependencies.environments import environment_production

from .source_backends import SourceBackendSANEScanner
from .utils import get_command_path_scanimage

BinaryDependency(
    environments=(environment_production,),
    label=_(message='SANE scanimage'),
    help_text=_(
        message='Utility provided by the SANE package. Used to control the '
        'scanner and obtained the scanned document image.'
    ), module=__name__, name='scanimage',
    path=get_command_path_scanimage(
        dotted_name=SourceBackendSANEScanner.backend_class_path
    )
)
