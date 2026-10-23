from mayan.apps.dependencies.classes import PythonDependency
from mayan.apps.dependencies.environments import environment_production

PythonDependency(
    environments=(environment_production,), module=__name__,
    name='django-auth-ldap', version_string='==5.3.0'
)
PythonDependency(
    environments=(environment_production,), module=__name__,
    name='django-axes[ipware]', version_string='==8.3.1'
)
