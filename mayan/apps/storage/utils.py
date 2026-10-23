import dbm
import logging
import os
from pathlib import Path
import shutil
import tempfile
import uuid

from django.apps import apps
from django.utils.module_loading import import_string

from .classes import DefinedStorage, PassthroughStorage
from .settings import setting_temporary_directory

logger = logging.getLogger(name=__name__)


def NamedTemporaryFile(*args, **kwargs):
    kwargs.update(
        {'dir': setting_temporary_directory.value}
    )
    return tempfile.NamedTemporaryFile(*args, **kwargs)


class PassthroughStorageProcessor:
    def __init__(
        self, app_label, defined_storage_name, log_file, model_name,
        file_attribute='file'
    ):
        self.app_label = app_label
        self.defined_storage_name = defined_storage_name
        self.file_attribute = file_attribute
        self.log_file = log_file
        self.model_name = model_name

    def _update_entry(self, key):
        if not self.reverse:
            self.database[key] = '1'
        else:
            try:
                del self.database[key]
            except KeyError:
                pass

    def _inclusion_condition(self, key):
        if self.reverse:
            return key in self.database
        else:
            return key not in self.database

    def execute(self, reverse=False):
        self.reverse = reverse
        model = apps.get_model(
            app_label=self.app_label, model_name=self.model_name
        )

        storage_instance = DefinedStorage.get(
            name=self.defined_storage_name
        ).get_storage_instance()

        if isinstance(storage_instance, PassthroughStorage):
            ContentType = apps.get_model(
                app_label='contenttypes', model_name='ContentType'
            )
            content_type = ContentType.objects.get_for_model(model=model)

            self.database = dbm.open(file=self.log_file, flag='c')

            try:
                for instance in model.objects.all():
                    key = '{}.{}'.format(content_type.name, instance.pk)
                    if self._inclusion_condition(key=key):
                        file_name = getattr(instance, self.file_attribute).name

                        content = storage_instance.open(
                            name=file_name, mode='rb',
                            _direct=not self.reverse
                        )
                        storage_instance.delete(name=file_name)
                        storage_instance.save(
                            _direct=self.reverse, content=content,
                            name=file_name
                        )
                        self._update_entry(key=key)
            finally:
                self.database.close()


def TemporaryDirectory(*args, **kwargs):
    kwargs.update(
        {'dir': setting_temporary_directory.value}
    )
    return tempfile.TemporaryDirectory(*args, **kwargs)


def TemporaryFile(*args, **kwargs):
    kwargs.update(
        {'dir': setting_temporary_directory.value}
    )
    return tempfile.TemporaryFile(*args, **kwargs)


def download_file_upload_to(instance, filename):
    return 'download-file-{}'.format(
        uuid.uuid4().hex
    )


def fs_cleanup(filename, suppress_exceptions=True):
    try:
        path = Path(filename)
        path.unlink()
    except OSError:
        try:
            shutil.rmtree(path=filename)
        except OSError:
            if suppress_exceptions:
                """Ignore exception."""
            else:
                raise


def get_storage_subclass(dotted_path):
    imported_storage_class = import_string(dotted_path=dotted_path)

    class StorageSubclass(imported_storage_class):
        def __init__(self, *args, **kwargs):
            return super().__init__(*args, **kwargs)

        def __eq__(self, other):
            return True

        def deconstruct(self):
            return (
                'mayan.apps.storage.classes.FakeStorageSubclass', (), {}
            )

    return StorageSubclass


def mkdtemp(*args, **kwargs):
    path = Path(setting_temporary_directory.value)

    if 'dir' in kwargs:
        path = path / kwargs['dir']

    kwargs.update(
        {'dir': path}
    )
    return tempfile.mkdtemp(*args, **kwargs)


def patch_files(path=None, replace_list=None):
    path_object = Path(path)
    for replace_entry in replace_list or []:
        path_entries = path_object.glob(
            '**/{}'.format(
                replace_entry['filename_pattern']
            )
        )
        for path_entry in path_entries:
            if path_entry.is_file():
                file_bytes = path_entry.read_bytes()
                for pattern in replace_entry['content_patterns']:
                    file_bytes = file_bytes.replace(
                        pattern['search'].encode('utf-8'),
                        pattern['replace'].encode('utf-8')
                    )
                path_entry.write_bytes(file_bytes)


def shared_uploaded_file_upload_to(instance, filename):
    return 'shared-file-{}'.format(
        uuid.uuid4().hex
    )


def touch(filename, times=None):
    with open(file=filename, mode='a'):
        os.utime(filename, times)
