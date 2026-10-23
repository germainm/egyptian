from django.utils.translation import gettext_lazy as _


class DependencyEnvironment:
    _registry = {}

    @classmethod
    def get(cls, name):
        return cls._registry[name]

    @classmethod
    def get_all(cls):
        environment_list = cls._registry.values()

        return sorted(
            environment_list, key=lambda environment: environment.name
        )

    def __init__(self, label, name, help_text=None, mark_missing=False):
        self.label = label
        self.help_text = help_text
        self.name = name
        self.mark_missing = mark_missing

        self.__class__._registry[name] = self

    def __str__(self):
        return str(self.label)

    def get_requirements_filename(self):
        return '{}.txt'.format(self.name)


environment_build = DependencyEnvironment(
    help_text=_(
        message='Environment used for building distributable packages of '
        'the software. End users can ignore missing dependencies under this '
        'environment.'
    ), label=_(message='Build'), name='build'
)
environment_development = DependencyEnvironment(
    help_text=_(
        message='Environment used for developers to make code changes. End '
        'users can ignore missing dependencies under this environment.'
    ), label=_(message='Development'), name='development'
)
environment_documentation = DependencyEnvironment(
    help_text=_(
        message='Environment used for building the documentation. End users '
        'can ignore missing dependencies under this environment.'
    ), label=_(message='Documentation'), name='documentation'
)
environment_documentation_override = DependencyEnvironment(
    help_text=_(
        message='Environment used to specify direct documentation '
        'dependencies to workaround unpinned or immutable dependency bugs '
        'in third party libraries. End users can ignore missing dependencies '
        'under this environment.'
    ), label=_(message='Documentation (override)'),
    name='documentation_override'
)
environment_linting = DependencyEnvironment(
    help_text=_(
        message='Environment used for running code linters and style checkers '
        'to ensure code quality and formatting compliance. Dependencies in this '
        'environment are not needed for normal production usage.'
    ),
    label=_(message='Linting'),
    name='linting'
)
environment_production = DependencyEnvironment(
    help_text=_(
        message='Normal environment for end users. A missing dependency '
        'under this environment will result in issues and errors during '
        'normal use.'
    ), label=_(message='Production'), mark_missing=True, name='production'
)
environment_publish = DependencyEnvironment(
    help_text=_(
        message='Environment used for publishing redistributable packages of '
        'the software. End users can ignore missing dependencies under this '
        'environment.'
    ), label=_(message='Publish'), name='publish'
)
environment_testing = DependencyEnvironment(
    help_text=_(
        message='Environment used running the test suit to verify the '
        'functionality of the code. Dependencies in this environment are not '
        'needed for normal production usage.'
    ), label=_(message='Testing'), name='testing'
)
