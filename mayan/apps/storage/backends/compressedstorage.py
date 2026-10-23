from io import UnsupportedOperation
import zipfile

try:
    import zlib
    COMPRESSION = zipfile.ZIP_DEFLATED
except ImportError:
    COMPRESSION = zipfile.ZIP_STORED

from django.core.files.base import ContentFile
from django.utils.encoding import force_str

from ..classes import BufferedFile, PassthroughStorage

from .literals import ZIP_CHUNK_SIZE, ZIP_MEMBER_FILENAME


class BufferedZipFile(BufferedFile):
    def __init__(self, *args, **kwargs):
        self.member_name = kwargs.pop('member_name')
        super().__init__(*args, **kwargs)
        self.binary_mode = 'b' in self.mode

        if 'r' in self.mode:
            self.zip_mode = 'r'
        else:
            self.zip_mode = 'w'

        self.zip_container_file_object = zipfile.ZipFile(
            file=self.file_object, mode=self.zip_mode
        )
        self.zip_file_object = self._get_zip_file_object()

    def _get_file_object_chunk(self):
        chunk = self.zip_file_object.read(n=ZIP_CHUNK_SIZE)

        if chunk:
            if self.binary_mode:
                return chunk
            else:
                return force_str(s=chunk)

    def _get_zip_file_object(self):
        return self.zip_container_file_object.open(
            name=self.member_name, mode=self.zip_mode
        )

    def _source_reset(self):
        if self.zip_mode == 'w':
            raise UnsupportedOperation(
                'Zip compressed files opened for writing cannot be '
                'rewound.'
            )

        self.zip_file_object.close()
        self.zip_file_object = self._get_zip_file_object()

    def close(self):
        self.zip_file_object.close()
        self.zip_container_file_object.close()
        super().close()

    def write(self, data):
        count = self.zip_file_object.write(data=data)
        self.position = self.position + count
        return count


class ZipCompressedPassthroughStorage(PassthroughStorage):
    def open(self, name, mode='rb', _direct=False):
        next_kwargs = {'name': name}

        if _direct:
            next_kwargs['mode'] = mode

            if issubclass(self.next_storage_class, PassthroughStorage):
                next_kwargs.update(
                    {'_direct': _direct}
                )

            return self._call_backend_method(
                method_name='open', kwargs=next_kwargs
            )
        else:
            next_kwargs['mode'] = 'rb+'

            storage_file = self._call_backend_method(
                method_name='open', kwargs=next_kwargs
            )

            return BufferedZipFile(
                file_object=storage_file, member_name=ZIP_MEMBER_FILENAME,
                mode=mode
            )

    def save(self, name, content, max_length=None, _direct=False):
        next_kwargs = {'max_length': max_length, 'name': name}
        if _direct:
            next_kwargs['content'] = content

            if issubclass(self.next_storage_class, PassthroughStorage):
                next_kwargs.update(
                    {'_direct': _direct}
                )

            return self._call_backend_method(
                method_name='save', kwargs=next_kwargs
            )
        else:
            if not self._call_backend_method(
                method_name='exists', kwargs={'name': name}
            ):
                name = self._call_backend_method(
                    method_name='save', kwargs={
                        'content': ContentFile(content=b''), 'name': name
                    }
                )

            with self._call_backend_method(
                method_name='open', kwargs={
                    'name': name, 'mode': 'wb'
                }
            ) as file_object:
                with zipfile.ZipFile(file=file_object, mode='w', compression=COMPRESSION) as zip_file_object:
                    zip_file_object.writestr(
                        zinfo_or_arcname=ZIP_MEMBER_FILENAME,
                        data=content.read()
                    )

                    for file in zip_file_object.filelist:
                        file.create_system = 0

            return name
