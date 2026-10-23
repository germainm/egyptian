import logging

from django.utils.translation import gettext_lazy as _

from .exceptions import InitializationStepError

logger = logging.getLogger(name=__name__)


class Runlevel:
    _registry = {}

    @classmethod
    def get(cls, name):
        return cls._registry[name]

    @classmethod
    def get_all(cls):
        return sorted(
            cls._registry.values(), key=lambda instance: instance.weight
        )

    def __init__(self, name, weight, label=None):
        if name in self.__class__._registry:
            raise InitializationStepError(
                'A runlevel with the name `{}` already exists.'.format(name)
            )

        self.name = name
        self.weight = weight
        self.label = label
        self.__class__._registry[name] = self

    def __repr__(self):
        return '<Runlevel: {}>'.format(self.name)


runlevel_preparation = Runlevel(
    name='preparation', weight=50, label=_(message='Preparation')
)
runlevel_database = Runlevel(
    name='database', weight=100, label=_(message='Database')
)
runlevel_dependencies = Runlevel(
    name='dependencies', weight=200, label=_(message='Dependencies')
)
runlevel_core = Runlevel(
    name='core', weight=300, label=_(message='Core')
)
runlevel_bootstrap = Runlevel(
    name='bootstrap', weight=400, label=_(message='Bootstrap data')
)
runlevel_maintenance = Runlevel(
    name='maintenance', weight=500, label=_(message='Maintenance')
)
