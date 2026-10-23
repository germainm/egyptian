from django.utils.translation import gettext_lazy as _

from mayan.apps.dependencies.classes import BinaryDependency
from mayan.apps.dependencies.environments import environment_production

from .backends.python_gnupg import gpg_path

BinaryDependency(
    environments=(environment_production,),
    label=_(message='GNU privacy guard'),
    help_text=_(
        message='GNU privacy guard - a PGP implementation.'
    ), module=__name__, name='gnupg', path=gpg_path
)
