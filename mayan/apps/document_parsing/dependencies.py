from django.utils.translation import gettext_lazy as _

from mayan.apps.dependencies.classes import BinaryDependency
from mayan.apps.dependencies.environments import environment_production

from .settings import setting_pdftotext_path

BinaryDependency(
    environments=(environment_production,),
    help_text=_(
        message='Utility from the poppler-utils package used to extract '
        'content from PDF files.'
    ), label=_(message='PDF to text'), module=__name__, name='pdftotext',
    path=setting_pdftotext_path.value
)
