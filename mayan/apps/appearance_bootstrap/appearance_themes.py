from django.utils.translation import gettext_lazy as _

from mayan.apps.appearance.classes import Theme

theme_flatly = Theme(
    default=True, label=_(message='Flatly'), name='flatly',
    stylesheet='appearance_bootstrap/node_modules/bootswatch/dist/flatly/bootstrap.min.css'
)
