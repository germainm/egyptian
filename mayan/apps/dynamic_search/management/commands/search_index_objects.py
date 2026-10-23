from django.core.management.base import BaseCommand

from mayan.apps.common.utils import parse_range

from ...search_models import SearchModel
from ...tasks import task_index_instances


class Command(BaseCommand):
    help = 'Index a list of objects.'
    missing_args_message = 'You must provide a search model name and an ID range.'

    def add_arguments(self, parser):
        parser.add_argument(
            dest='model_name', help='Name of search model to index.',
            metavar='<model name>'
        )
        parser.add_argument(
            dest='id_range_string', help='Range of IDs to index.',
            metavar='<ID range>'
        )

    def handle(self, model_name, id_range_string, **options):
        try:
            search_model = SearchModel.get(name=model_name)
        except KeyError:
            self.stderr.write(
                msg='Unknown search model `{}`'.format(model_name)
            )
            exit(1)

        try:
            parse_range(range_string=id_range_string)
        except ValueError as exception:
            self.stderr.write(
                msg='Unknown or invalid range format `{}`; {}'.format(
                    id_range_string, exception
                )
            )
            exit(1)

        count_queued = 0

        for id_list in search_model.get_id_groups(range_string=id_range_string):
            task_index_instances.apply_async(
                kwargs={
                    'id_list': id_list,
                    'search_model_full_name': search_model.full_name
                }
            )

            count_queued = count_queued + len(id_list)

        self.stdout.write(
            msg='\nInstances queued for indexing: {}'.format(count_queued)
        )
