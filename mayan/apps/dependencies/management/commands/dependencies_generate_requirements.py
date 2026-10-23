from pathlib import Path

from django.core import management
from django.utils.translation import gettext_lazy as _

from ...classes import PythonDependency
from ...environments import DependencyEnvironment
from ...literals import (
    MESSAGE_REQUIREMENTS_CHECK_PATH_MISSING,
    MESSAGE_REQUIREMENTS_DESTINATION_MISSING,
    MESSAGE_REQUIREMENTS_FILE_OUTDATED, MESSAGE_REQUIREMENTS_OUTDATED,
    MESSAGE_REQUIREMENTS_UNKNOWN_ENVIRONMENT
)


class Command(management.BaseCommand):
    help = 'Generate Python requirement files.'

    def add_arguments(self, parser):
        parser.add_argument(
            'environment', nargs='?', help=_(
                message='Name of the environment to generate. Every declared '
                'environment is generated when this is omitted.'
            )
        )
        parser.add_argument(
            '--check', action='store_true', dest='check', help=_(
                message='Do not write anything. Exit with an error when a '
                'requirement file does not match the dependencies declared '
                'for its environment.'
            )
        )
        parser.add_argument(
            '--exclude', action='store', dest='exclude', help=_(
                message='Comma separated names of dependencies to exclude '
                'from the list generated.'
            ),
        )
        parser.add_argument(
            '--only', action='store', dest='only', help=_(
                message='Comma separated names of dependencies to show in '
                'the list while excluding every other one.'
            ),
        )
        parser.add_argument(
            '--path', action='store', dest='path', help=_(
                message='Directory the requirement files are written to. '
                'Each environment is written to a file named after it. The '
                'requirements are printed instead when this is omitted.'
            )
        )

    def get_environment_list(self, environment_name):
        if environment_name is None:
            return DependencyEnvironment.get_all()

        try:
            environment = DependencyEnvironment.get(name=environment_name)
        except KeyError:
            environment_name_list = [
                environment.name for environment in
                DependencyEnvironment.get_all()
            ]
            raise management.CommandError(
                MESSAGE_REQUIREMENTS_UNKNOWN_ENVIRONMENT % {
                    'environment': environment_name,
                    'environment_list': ', '.join(environment_name_list)
                }
            )

        return [environment]

    def get_requirement_text(self, environment, exclude_list, only_list):
        dependency_list = PythonDependency.get_for_attribute(
            attribute_name='environments.name',
            attribute_value=environment.name, subclass_only=True
        )
        line_list = []

        for dependency in dependency_list:
            if only_list and dependency.name not in only_list:
                continue

            if dependency.name in exclude_list:
                continue

            line_list.append(
                '{}{}\n'.format(dependency.name, dependency.version_string)
            )

        return ''.join(line_list)

    def handle(self, *args, **options):
        check = options['check']
        path = options['path']

        if options['environment'] is None and not path:
            raise management.CommandError(
                str(MESSAGE_REQUIREMENTS_DESTINATION_MISSING)
            )

        if check and not path:
            raise management.CommandError(
                str(MESSAGE_REQUIREMENTS_CHECK_PATH_MISSING)
            )

        environment_list = self.get_environment_list(
            environment_name=options['environment']
        )
        exclude_list = (options['exclude'] or '').split(',')
        only_list = [
            name for name in (options['only'] or '').split(',') if name
        ]
        outdated_filename_list = []

        for environment in environment_list:
            requirement_text = self.get_requirement_text(
                environment=environment, exclude_list=exclude_list,
                only_list=only_list
            )

            if not path:
                self.stdout.write(msg=requirement_text, ending='')
                continue

            filename = environment.get_requirements_filename()
            file_path = Path(path, filename)

            if check:
                try:
                    existing_text = file_path.read_text()
                except FileNotFoundError:
                    existing_text = None

                if existing_text != requirement_text:
                    outdated_filename_list.append(filename)
                    self.stderr.write(
                        msg=str(
                            MESSAGE_REQUIREMENTS_FILE_OUTDATED % {
                                'environment': environment.name,
                                'filename': filename
                            }
                        )
                    )
            else:
                file_path.write_text(data=requirement_text)

        if outdated_filename_list:
            raise management.CommandError(
                str(
                    MESSAGE_REQUIREMENTS_OUTDATED % {
                        'filename_list': ', '.join(outdated_filename_list)
                    }
                )
            )
