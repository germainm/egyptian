from django.apps import apps
from django.contrib.staticfiles.management.commands.collectstatic import (
    Command as DjangoCommand
)


class Command(DjangoCommand):
    help = 'Call the collectstatic command with some specific defaults.'

    def handle(self, **options):
        self.verbosity = options['verbosity']

        for key, data in apps.app_configs.items():
            options['ignore_patterns'].extend(
                getattr(
                    data, 'static_media_ignore_patterns', ()
                )
            )

        if options['verbosity'] >= 2:
            self.log(
                'Ignore patterns: {}'.format(
                    options['ignore_patterns']
                ), level=2
            )

        return super().handle(**options)
