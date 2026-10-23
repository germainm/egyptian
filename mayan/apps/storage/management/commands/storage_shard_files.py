import os

from django.core import management

from ...backends.sharded_storages import (
    ShardedDirectoryFileSystemStorageMixin
)
from ...classes import DefinedStorage


class Command(management.BaseCommand):
    help = (
        'Move the files of a defined storage into the shard directories of '
        'the sharded directory storage backend. Stop the instance before '
        'running this command.'
    )
    missing_args_message = 'You must provide a defined storage name.'

    def add_arguments(self, parser):
        parser.add_argument(
            dest='storage_name', help='Name of the defined storage.',
            metavar='<storage name>'
        )
        parser.add_argument(
            '--dry-run', action='store_true', dest='dry_run', help='Show '
            'the changes without performing them.'
        )
        parser.add_argument(
            '--remove-orphan-files', action='store_true',
            dest='remove_orphan_files', help='Remove the empty files left '
            'in the shard directories by a previous version of the sharded '
            'directory storage backend.'
        )

    def _do_empty_directory_remove(self, location):
        result = 0

        for path_directory, directory_name_list, file_name_list in os.walk(
            location, topdown=False
        ):
            if path_directory == location:
                continue

            try:
                os.rmdir(path_directory)
            except OSError:
                """
                The directory is not empty. Nothing to do.
                """
            else:
                result = result + 1

        return result

    def _get_entry_list(self, location):
        result = []

        for path_directory, directory_name_list, file_name_list in os.walk(
            location
        ):
            for file_name in file_name_list:
                path_file = os.path.join(path_directory, file_name)

                name = os.path.relpath(path_file, location)

                name_normalized = name.replace(os.sep, '/')

                result.append(name_normalized)

        return sorted(result)

    def _get_name_base_name_count(self, name_list):
        result = {}

        for name in name_list:
            base_name = self._get_name_base_name(name=name)

            count_previous = result.get(base_name, 0)

            result[base_name] = count_previous + 1

        return result

    def _get_name_base_name(self, name):
        return name.rpartition('/')[2]

    def _get_name_is_legacy_sharded(self, name):
        part_list = name.split('/')

        base_name = part_list[-1]
        directory_name_list = part_list[:-1]

        if not directory_name_list:
            return False

        for level, directory_name in enumerate(directory_name_list, start=1):
            if directory_name != base_name[:level]:
                return False

        return True

    def _get_path_absolute(self, location, name):
        part_list = name.split('/')

        return os.path.join(location, *part_list)

    def _get_storage_instance(self, storage_name):
        try:
            defined_storage = DefinedStorage.get(name=storage_name)
        except KeyError:
            self.stderr.write(
                msg='Unknown defined storage `{}`.'.format(storage_name)
            )
            exit(1)

        storage_instance = defined_storage.get_storage_instance()

        if not isinstance(
            storage_instance, ShardedDirectoryFileSystemStorageMixin
        ):
            self.stderr.write(
                msg='The defined storage `{}` does not use a sharded '
                'directory storage backend.'.format(storage_name)
            )
            exit(1)

        return storage_instance

    def handle(self, storage_name, **options):
        dry_run = options['dry_run']
        remove_orphan_files = options['remove_orphan_files']

        storage_instance = self._get_storage_instance(
            storage_name=storage_name
        )

        location = storage_instance.location

        name_list = self._get_entry_list(location=location)

        base_name_count = self._get_name_base_name_count(name_list=name_list)

        count_moved = 0
        count_removed = 0
        count_skipped = 0

        for name in name_list:
            path_source = self._get_path_absolute(
                location=location, name=name
            )

            if '/' in name:
                if not remove_orphan_files:
                    continue

                if not self._get_name_is_legacy_sharded(name=name):
                    continue

                base_name = self._get_name_base_name(name=name)

                if base_name_count[base_name] < 2:
                    continue

                file_size = os.path.getsize(path_source)

                if file_size != 0:
                    continue

                self.stdout.write(
                    msg='Removing orphan file `{}`.'.format(name)
                )

                if not dry_run:
                    os.remove(path_source)

                count_removed = count_removed + 1

                continue

            sharded_name = storage_instance.get_sharded_name(name=name)

            if sharded_name == name:
                continue

            path_target = self._get_path_absolute(
                location=location, name=sharded_name
            )

            if os.path.exists(path_target):
                self.stdout.write(
                    msg='Skipping `{}`, the file `{}` already exists.'.format(
                        name, sharded_name
                    )
                )

                count_skipped = count_skipped + 1

                continue

            self.stdout.write(
                msg='Moving `{}` to `{}`.'.format(name, sharded_name)
            )

            if not dry_run:
                path_target_directory = os.path.dirname(path_target)

                os.makedirs(path_target_directory, exist_ok=True)

                os.rename(path_source, path_target)

            count_moved = count_moved + 1

        if dry_run:
            count_directory_removed = 0
        else:
            count_directory_removed = self._do_empty_directory_remove(
                location=location
            )

        self.stdout.write(
            msg='\nFiles moved: {}, files skipped: {}, orphan files '
            'removed: {}, empty directories removed: {}.'.format(
                count_moved, count_skipped, count_removed,
                count_directory_removed
            )
        )
