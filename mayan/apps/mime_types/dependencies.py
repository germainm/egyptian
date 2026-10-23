from django.utils.translation import gettext_lazy as _

from mayan.apps.dependencies.classes import BinaryDependency
from mayan.apps.dependencies.environments import environment_production

from .backends.literals import DEFAULT_FILE_PATH, DEFAULT_MIMETYPE_PATH

BinaryDependency(
    environments=(environment_production,),
    label=_(message='File::MimeInfo'), help_text=_(
        message='This module can be used to determine the MIME type of a '
        'file. It tries to implement the freedesktop specification for a '
        'shared MIME database.'
    ), module=__name__, name='libfile-mimeinfo-perl',
    path=DEFAULT_MIMETYPE_PATH
)
BinaryDependency(
    environments=(environment_production,),
    label=_(message='file'), help_text=_(
        message='determine file type using content tests'
    ), module=__name__, name='file', path=DEFAULT_FILE_PATH
)
