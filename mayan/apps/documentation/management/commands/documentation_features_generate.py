from django.core import management

from ...classes import FeaturePage


class Command(management.BaseCommand):
    help = 'Generate the documentation Features page from the app fragments.'

    def handle(self, *args, **options):
        label_list_uncategorized = FeaturePage.do_write()

        if label_list_uncategorized:
            self.stderr.write(
                self.style.WARNING(
                    'Uncategorized feature apps: {}'.format(
                        ', '.join(label_list_uncategorized)
                    )
                )
            )
