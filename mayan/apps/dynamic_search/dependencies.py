from mayan.apps.dependencies.classes import PythonDependency
from mayan.apps.dependencies.environments import environment_production

PythonDependency(
    environments=(environment_production,), module=__name__, name='Whoosh',
    version_string='==2.7.4'
)
PythonDependency(
    environments=(environment_production,), module=__name__,
    name='dateparser', version_string='==1.4.0'
)
PythonDependency(
    environments=(environment_production,), module=__name__,
    name='elasticsearch', version_string='==9.4.0'
)
