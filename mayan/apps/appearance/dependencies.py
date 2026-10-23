from django.utils.translation import gettext_lazy as _

from mayan.apps.dependencies.classes import JavaScriptDependency
from mayan.apps.dependencies.environments import environment_production

JavaScriptDependency(
    environments=(environment_production,), label=_(message='Fancybox'),
    module=__name__, name='@fancyapps/fancybox', version_string='=3.3.5'
)
JavaScriptDependency(
    environments=(environment_production,), label=_(message='jQuery'),
    module=__name__, name='jquery', version_string='=3.7.1'
)
JavaScriptDependency(
    environments=(environment_production,), label=_(message='JQuery Form'),
    module=__name__, name='jquery-form', version_string='=4.3.0'
)
JavaScriptDependency(
    environments=(environment_production,), label=_(message='Select 2'),
    module=__name__, name='select2', version_string='=4.0.13'
)
