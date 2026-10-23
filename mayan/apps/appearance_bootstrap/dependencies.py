from django.utils.translation import gettext_lazy as _

from mayan.apps.dependencies.classes import (
    GoogleFontDependency, JavaScriptDependency
)
from mayan.apps.dependencies.environments import environment_production

GoogleFontDependency(
    environments=(environment_production,), label=_(message='Lato font'),
    module=__name__, name='lato', url='https://fonts.googleapis.com/css?family=Lato:400,700,400italic'
)

JavaScriptDependency(
    environments=(environment_production,), label=_(message='Bootstrap'),
    module=__name__, name='bootstrap', version_string='=5.3.8'
)
JavaScriptDependency(
    environments=(environment_production,), label=_(message='Bootswatch'),
    module=__name__, name='bootswatch',
    replace_list=[
        {
            'filename_pattern': 'bootstrap.*.css',
            'content_patterns': [
                {
                    'search': 'https://fonts.googleapis.com/css2?family=Lato:ital,wght@0,400;0,700;1,400&display=swap',
                    'replace': '../../../../google_fonts/lato/import.css'
                }
            ]
        }
    ],
    version_string='=5.3.8'
)
