from io import BytesIO, StringIO
import logging
import os

from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.class_mixins import AppsModuleLoaderMixin

from .literals import BUFFERED_FILE_SEEK_BLOCK_SIZE, DEFAULT_STORAGE_BACKEND

logger = logging.getLogger(name=__name__)


class BufferedFile(File):
    def __init__(self, file_object, mode, name=None):
        self.file_object = file_object
        self.mode = mode
        self.name = name
        self._stream_initialize()

    def _get_file_object_chunk(self):
        raise NotImplementedError(
            'Subclasses must return the next decoded chunk of the source '
            'file object or `None` when it is exhausted.'
        )

    def _read_and_discard(self, count=None):
        while count is None or count > 0:
            if count is None:
                size = BUFFERED_FILE_SEEK_BLOCK_SIZE
            else:
                size = min(count, BUFFERED_FILE_SEEK_BLOCK_SIZE)

            data = self.read(size)

            if not data:
                break

            if count is not None:
                count = count - len(data)

    def _source_reset(self):
        self.file_object.seek(0)

    def _stream_initialize(self):
        if 'b' in self.mode:
            self.stream = BytesIO()
        else:
            self.stream = StringIO()

        self.stream_size = 0
        self.position = 0

    def close(self):
        self.file_object.close()
        self.stream.close()

    @property
    def closed(self):
        return self.stream.closed

    def flush(self):
        return self.file_object.flush()

    def read(self, size=None):
        if size is None or size < 0:
            size = -1

        while size == -1 or self.stream_size < size:
            chunk = self._get_file_object_chunk()
            if chunk:
                position = self.stream.tell()
                self.stream.seek(0, 2)
                self.stream.write(chunk)
                self.stream_size += len(chunk)
                self.stream.seek(position)
            else:
                break

        if size == -1:
            read_size = None
        else:
            read_size = min(size, self.stream_size)

        data = self.stream.read(read_size)
        self.stream_size -= len(data)
        self.position = self.position + len(data)
        return data

    def readable(self):
        if self.closed:
            return False

        return 'r' in self.mode or '+' in self.mode

    def seek(self, offset, whence=os.SEEK_SET):
        if whence == os.SEEK_SET:
            position_target = offset
        elif whence == os.SEEK_CUR:
            position_target = self.position + offset
        elif whence == os.SEEK_END:
            position_target = self.size + offset
        else:
            raise ValueError(
                'Unsupported whence value: {}'.format(whence)
            )

        if position_target < 0:
            raise ValueError(
                'Negative seek position: {}'.format(position_target)
            )

        if position_target < self.position:
            self.reset()

        self._read_and_discard(count=position_target - self.position)

        return self.position

    def seekable(self):
        return not self.closed

    def reset(self):
        self._source_reset()
        self.stream.close()
        self._stream_initialize()

    @cached_property
    def size(self):
        position_original = self.position

        self.reset()
        self._read_and_discard()

        result = self.position

        self.reset()
        self._read_and_discard(count=position_original)

        return result

    def tell(self):
        return self.position

    def writable(self):
        if self.closed:
            return False

        return 'a' in self.mode or 'w' in self.mode or '+' in self.mode


class DefinedStorage(AppsModuleLoaderMixin):
    _loader_module_name = 'storages'
    _registry = {}

    @classmethod
    def get(cls, name):
        return cls._registry[name]

    def __init__(
        self, dotted_path, label, name, kwargs=None, error_message=None
    ):
        self.dotted_path = dotted_path
        self.error_message = error_message
        self.label = label
        self.name = name
        self.kwargs = kwargs or {}
        self.__class__._registry[name] = self

    def __eq__(self, other):
        return True

    def get_storage_instance(self):
        storage_subclass = self.get_storage_subclass()

        try:
            return storage_subclass(**self.kwargs)
        except Exception as exception:
            message_default = _(
                message='Unable to initialize storage: %(name)s. Check the '
                'storage backend dotted path and arguments.'
            ) % {'name': self.name}

            message = self.error_message or message_default

            message_final = format_lazy(
                '{}; {}; {}', message, exception, self.kwargs
            )

            logger.fatal(message_final)
            raise TypeError(message_final) from exception

    def get_storage_subclass(self):
        try:
            imported_storage_class = import_string(
                dotted_path=self.dotted_path
            )
        except Exception as exception:
            message_default = _(
                message='Unable to import storage class: %(name)s. Check '
                'the storage backend dotted path.'
            ) % {'name': self.name}

            message = self.error_message or message_default

            message_final = format_lazy('{}; {}', message, exception)

            logger.fatal(message_final)
            raise TypeError(message_final) from exception
        else:
            class DynamicStorageSubclass(imported_storage_class):
                def __init__(self, *args, **kwargs):
                    return super().__init__(*args, **kwargs)

                def __eq__(self, other):
                    return True

                def deconstruct(self):
                    return (
                        'mayan.apps.storage.classes.FakeStorageSubclass', (), {}
                    )

            return DynamicStorageSubclass


def defined_storage_proxy_method(method_name):
    def inner_function(self, *args, **kwargs):
        storage_class = DefinedStorage.get(name=self.name)
        storage_instance = storage_class.get_storage_instance()
        storage_attribute = getattr(storage_instance, method_name)

        return storage_attribute(*args, **kwargs)

    return inner_function


@deconstructible
class DefinedStorageLazy:
    def __init__(self, name):
        self.name = name
        super().__init__()

    delete = defined_storage_proxy_method(method_name='delete')
    exists = defined_storage_proxy_method(method_name='exists')
    generate_filename = defined_storage_proxy_method(
        method_name='generate_filename'
    )
    open = defined_storage_proxy_method(method_name='open')
    save = defined_storage_proxy_method(method_name='save')
    size = defined_storage_proxy_method(method_name='size')

    def path(self, *args, **kwargs):
        storage_class = DefinedStorage.get(name=self.name)
        storage_instance = storage_class.get_storage_instance()

        try:
            return storage_instance.path(*args, **kwargs)
        except NotImplementedError:
            raise NotImplementedError(
                'The storage backend for the defined storage "{}" does '
                'not support absolute local filesystem paths. This '
                'happens when using a remote or object storage backend '
                '(e.g. S3). Access the file content via the `.open()` '
                'method instead of assuming a local path.'.format(
                    self.name
                )
            )


class FakeStorageSubclass:
    def __eq__(self, other):
        return True


class PassthroughStorage(Storage):
    def __init__(self, *args, **kwargs):
        logger.debug(
            'initializing passthrough storage with: %s, %s', args, kwargs
        )
        next_storage_backend = kwargs.pop(
            'next_storage_backend', DEFAULT_STORAGE_BACKEND
        )
        next_storage_backend_arguments = kwargs.pop(
            'next_storage_backend_arguments', {}
        )

        self.next_storage_class = import_string(
            dotted_path=next_storage_backend
        )

        self.next_storage_backend = self.next_storage_class(
            **next_storage_backend_arguments
        )
        super().__init__(*args, **kwargs)

    def _call_backend_method(self, method_name, kwargs):
        return getattr(self.next_storage_backend, method_name)(**kwargs)

    def delete(self, *args, **kwargs):
        return self.next_storage_backend.delete(*args, **kwargs)

    def exists(self, *args, **kwargs):
        return self.next_storage_backend.exists(*args, **kwargs)

    def path(self, *args, **kwargs):
        return self.next_storage_backend.path(*args, **kwargs)

    def size(self, *args, **kwargs):
        return self.next_storage_backend.size(*args, **kwargs)
