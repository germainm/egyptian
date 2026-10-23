from mayan.apps.dependencies.classes import PythonDependency
from mayan.apps.dependencies.environments import environment_production

PythonDependency(
    environments=(environment_production,), module=__name__, name='gevent',
    version_string='==26.4.0'
)
PythonDependency(
    environments=(environment_production,), module=__name__, name='greenlet',
    version_string='==3.5.0'
)
PythonDependency(
    environments=(environment_production,), module=__name__, name='gunicorn',
    version_string='==26.0.0'
)
PythonDependency(
    environments=(environment_production,), module=__name__,
    name='whitenoise', version_string='==6.12.0'
)
