import email
from io import BytesIO
import logging
import tarfile
import zipfile

import extract_msg
from pypdf import PdfReader

try:
    import zlib  # NOQA
    COMPRESSION = zipfile.ZIP_DEFLATED
except ImportError:
    COMPRESSION = zipfile.ZIP_STORED

from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.encoding import force_bytes, force_str

from mayan.apps.mime_types.classes import MIMETypeBackend

from .exceptions import (
    ArchiveCompressionRatioExceeded, ArchiveInputSizeExceeded,
    ArchiveMemberSizeExceeded, NoMIMETypeMatch
)
from .literals import MIME_TYPE_EML, MSG_MIME_TYPES

logger = logging.getLogger(name=__name__)


class Archive:
    _registry = {}

    @staticmethod
    def _get_seekable_size(file_object):
        """
        Return the size in bytes of a seekable file-like object by seeking
        to end and back to the original position. Returns ``None`` if the
        object is not seekable (no ``seek``/``tell``), in which case the
        size check is skipped, the caller is responsible for any further
        bounded reads.
        """
        try:
            original_position = file_object.tell()
            file_object.seek(0, 2)
            size = file_object.tell()
            file_object.seek(original_position)
        except (AttributeError, OSError):
            return None
        else:
            return size

    @classmethod
    def register(cls, mime_types, archive_classes):
        for mime_type in mime_types:
            for archive_class in archive_classes:
                cls._registry.setdefault(
                    mime_type, []
                ).append(archive_class)

    @classmethod
    def open(cls, file_object):
        mime_type = MIMETypeBackend.get_backend_instance().get_mime_type(
            file_object=file_object, mime_type_only=True
        )[0]

        try:
            archives_classes = cls._registry[mime_type]
        except KeyError:
            raise NoMIMETypeMatch
        else:
            for archive_class in archives_classes:
                instance = archive_class()
                instance._open(file_object=file_object)
                return instance

    def _check_compression_ratio(self, uncompressed_size, compressed_size):
        """
        Refuse a member whose declared-to-compressed size ratio exceeds
        the configured maximum. ``compressed_size`` of zero (e.g.
        directory entries, zero-byte files) is treated as a 1:1 ratio
        to avoid division by zero and false positives on legitimately
        empty members.
        """
        # Local import to avoid a circular import at module load time:
        # settings.py imports from literals.py which is in this app.
        from .settings import (
            setting_compressed_file_compression_ratio_maximum
        )

        ratio_maximum = (
            setting_compressed_file_compression_ratio_maximum.value
        )
        if not ratio_maximum:
            return

        if compressed_size <= 0:
            return

        ratio = uncompressed_size / compressed_size
        if ratio > ratio_maximum:
            raise ArchiveCompressionRatioExceeded(
                'Archive member compression ratio {ratio:.0f} exceeds '
                'maximum {maximum}.'.format(
                    maximum=ratio_maximum, ratio=ratio
                )
            )

    def _check_input_size(self, file_object):
        """
        Refuse to parse an input archive whose size exceeds the
        configured maximum. Called from each subclass's ``_open``. A
        non-seekable input is allowed through (size unknown), the
        per-member checks and upstream-library memory limits provide
        the next line of defense.
        """
        from .settings import setting_compressed_file_input_size_maximum

        size_maximum = setting_compressed_file_input_size_maximum.value
        if not size_maximum:
            return

        input_size = Archive._get_seekable_size(file_object=file_object)
        if input_size is None:
            return

        if input_size > size_maximum:
            raise ArchiveInputSizeExceeded(
                'Archive input size {size} exceeds maximum '
                '{maximum}.'.format(
                    maximum=size_maximum, size=input_size
                )
            )

    def _check_member_size(self, member_size, filename=None):
        """
        Refuse a member whose declared (uncompressed) size exceeds the
        configured maximum.
        """
        from .settings import setting_compressed_file_member_size_maximum

        size_maximum = setting_compressed_file_member_size_maximum.value
        if not size_maximum:
            return

        if member_size > size_maximum:
            raise ArchiveMemberSizeExceeded(
                'Archive member {filename!r} size {size} exceeds '
                'maximum {maximum}.'.format(
                    filename=filename, maximum=size_maximum,
                    size=member_size
                )
            )

    def _open(self, file_object):
        raise NotImplementedError

    def add_file(self, file_object, filename):
        """
        Add a file as a member of an archive
        """
        raise NotImplementedError

    def close(self):
        self._archive.close()

    def create(self):
        """
        Create an empty archive
        """
        raise NotImplementedError

    def get_members(self):
        return (
            SimpleUploadedFile(
                content=self.member_contents(filename=filename),
                name=filename
            ) for filename in self.members()
        )

    def member_contents(self, filename):
        """
        Return the content of a member
        """
        raise NotImplementedError

    def members(self):
        """
        Return a list of all the elements inside the archive
        """
        raise NotImplementedError

    def open_member(self, filename):
        """
        Return a file-like object to a member of the archive
        """
        raise NotImplementedError


class EMLArchive(Archive):
    def _get_parts(self, message):
        counter = 1

        if message.is_multipart():
            for part in message.iter_parts():
                yield from self._get_parts(message=part)
        else:
            if message.is_attachment() or message.get_content_disposition() == 'inline':
                content = message.get_content()
                if len(content) != 0:
                    detected_filename = message.get_filename()
                    if detected_filename:
                        label = detected_filename
                    else:
                        label = 'attachment-{}'.format(counter)
                        counter += 1

                    yield {'label': label, 'message': message}
            else:
                # If it is not an attachment then it should be a body message
                # part.
                yield {'label': 'body', 'message': message}

    def _get_part_content(self, part, filename):
        """
        Return a part's content as bytes, after enforcing the
        per-member size cap. The EML parser has already materialized
        the part into memory by the time we get here; the cap defends
        downstream consumers, not this layer.
        """
        content = force_bytes(s=part['message'].get_content())
        self._check_member_size(
            filename=filename, member_size=len(content)
        )
        return content

    def _open(self, file_object):
        self._check_input_size(file_object=file_object)
        self._archive = email.message_from_binary_file(
            fp=file_object, policy=email.policy.default
        )

    def get_parts(self):
        yield from self._get_parts(message=self._archive)

    def member_contents(self, filename):
        for part in self.get_parts():
            if part['label'] == filename:
                return self._get_part_content(
                    filename=filename, part=part
                )

    def members(self):
        result = []
        for part in self.get_parts():
            result.append(
                part['label']
            )

        return result

    def open_member(self, filename):
        for part in self.get_parts():
            if part['label'] == filename:
                content = self._get_part_content(
                    filename=filename, part=part
                )
                return File(
                    file=BytesIO(initial_bytes=content),
                    name=filename
                )


class MsgArchive(Archive):
    def _open(self, file_object):
        self._check_input_size(file_object=file_object)
        self._archive = extract_msg.Message(path=file_object)

    def member_contents(self, filename):
        if filename == 'message.txt':
            content = force_bytes(s=self._archive.body)
            self._check_member_size(
                filename=filename, member_size=len(content)
            )
            return content

        for member in self._archive.attachments:
            if member.longFilename == filename:
                content = force_bytes(s=member.data)
                self._check_member_size(
                    filename=filename, member_size=len(content)
                )
                return content

    def members(self):
        results = []
        for attachments in self._archive.attachments:
            results.append(attachments.longFilename)

        if self._archive.body:
            results.append('message.txt')

        return results

    def open_member(self, filename):
        if filename == 'message.txt':
            content = force_bytes(s=self._archive.body)
            self._check_member_size(
                filename=filename, member_size=len(content)
            )
            return File(
                file=BytesIO(initial_bytes=content), name=filename
            )

        for member in self._archive.attachments:
            if member.longFilename == filename:
                content = force_bytes(s=member.data)
                self._check_member_size(
                    filename=filename, member_size=len(content)
                )
                return File(
                    file=BytesIO(initial_bytes=content), name=filename
                )


class PDFArchive(Archive):
    def _get_member_and_content_list(self):
        for name, content_list in self._archive.attachments.items():
            for index, content in enumerate(iterable=content_list):
                member_filename = '{index}-{name}'.format(
                    index=index, name=name
                )
                yield member_filename, content

    def _open(self, file_object):
        self._check_input_size(file_object=file_object)
        self._archive = PdfReader(stream=file_object)

    def member_contents(self, filename):
        for member_filename, content in self._get_member_and_content_list():
            if filename == member_filename:
                self._check_member_size(
                    filename=filename, member_size=len(content)
                )
                yield from content

    def members(self):
        result = [
            member_filename for member_filename, content in self._get_member_and_content_list()
        ]

        return result

    def open_member(self, filename):
        for member_filename, content in self._get_member_and_content_list():
            if filename == member_filename:
                initial_bytes = force_bytes(s=content)
                self._check_member_size(
                    filename=filename, member_size=len(initial_bytes)
                )
                buffer = BytesIO(initial_bytes=initial_bytes)
                return File(file=buffer, name=filename)


class TarArchive(Archive):
    def _open(self, file_object):
        self._check_input_size(file_object=file_object)
        self._archive = tarfile.open(fileobj=file_object)

    def _get_tarinfo(self, filename):
        """
        Resolve a member name to its ``TarInfo`` so callers can read
        the declared size before any decompression.
        """
        return self._archive.getmember(name=filename)

    def add_file(self, file_object, filename):
        self._archive.addfile(
            tarinfo=self._archive.gettarinfo(
                fileobj=file_object, arcname=filename
            ), fileobj=file_object
        )

    def create(self):
        self.string_buffer = BytesIO()
        # Mode cannot be a binary mode.
        self._archive = tarfile.TarFile(fileobj=self.string_buffer, mode='w')

    def member_contents(self, filename):
        tarinfo = self._get_tarinfo(filename=filename)
        self._check_member_size(
            filename=filename, member_size=tarinfo.size
        )
        return self._archive.extractfile(filename).read()

    def members(self):
        return self._archive.getnames()

    def open_member(self, filename):
        tarinfo = self._get_tarinfo(filename=filename)
        self._check_member_size(
            filename=filename, member_size=tarinfo.size
        )
        return self._archive.extractfile(filename)


class ZipArchive(Archive):
    def _open(self, file_object):
        self._check_input_size(file_object=file_object)
        self._archive = zipfile.ZipFile(file=file_object)

    def _get_zipinfo(self, filename):
        """
        Resolve a member name to its ``ZipInfo`` so callers can read
        the declared size and compressed size before any decompression.
        """
        return self._archive.getinfo(name=filename)

    def add_file(self, file_object, filename):
        self._archive.writestr(
            zinfo_or_arcname=filename, data=file_object.read(),
            compress_type=COMPRESSION
        )

    def create(self):
        self.string_buffer = BytesIO()
        # Mode cannot be a binary mode.
        self._archive = zipfile.ZipFile(file=self.string_buffer, mode='w')

    def member_contents(self, filename):
        zipinfo = self._get_zipinfo(filename=filename)
        self._check_member_size(
            filename=filename, member_size=zipinfo.file_size
        )
        self._check_compression_ratio(
            compressed_size=zipinfo.compress_size,
            uncompressed_size=zipinfo.file_size
        )
        return self._archive.read(name=filename)

    def members(self):
        results = []

        for filename in self._archive.namelist():
            # Zip files only support UTF-8 and CP437 encodings.
            # Attempt to decode CP437 to be able to check if it ends
            # with a slash.
            # Future improvement that violates the Zip format:
            # Add chardet.detect to detect the most likely encoding
            # if other than CP437.
            try:
                filename = filename.decode('CP437')
                is_unicode = False
            except AttributeError:
                filename = force_str(s=filename)
                is_unicode = True
            except UnicodeEncodeError:
                is_unicode = True

            if not filename.endswith('/'):
                # Re encode in the original encoding
                if not is_unicode:
                    filename = filename.encode(
                        encoding='CP437', errors='strict'
                    )

                results.append(filename)

        return results

    def open_member(self, filename):
        zipinfo = self._get_zipinfo(filename=filename)
        self._check_member_size(
            filename=filename, member_size=zipinfo.file_size
        )
        self._check_compression_ratio(
            compressed_size=zipinfo.compress_size,
            uncompressed_size=zipinfo.file_size
        )
        return self._archive.open(name=filename)

    def write(self, filename=None):
        # fix for Linux zip files read in Windows
        for entry in self._archive.filelist:
            entry.create_system = 0

        self.string_buffer.seek(0)

        if filename:
            with open(file=filename, mode='wb') as file_object:
                file_object.write(
                    self.string_buffer.read()
                )
        else:
            return self.string_buffer

    def as_file(self, filename):
        return SimpleUploadedFile(
            name=filename, content=self.write().read()
        )


Archive.register(
    archive_classes=(EMLArchive,), mime_types=MIME_TYPE_EML
)
Archive.register(
    archive_classes=(MsgArchive,), mime_types=MSG_MIME_TYPES
)
Archive.register(
    archive_classes=(PDFArchive,), mime_types=('application/pdf',)
)
Archive.register(
    archive_classes=(TarArchive,), mime_types=('application/x-tar',)
)
Archive.register(
    archive_classes=(TarArchive,), mime_types=('application/gzip',)
)
Archive.register(
    archive_classes=(TarArchive,), mime_types=(
        'application/x-bzip', 'application/x-bzip2'
    )
)
Archive.register(
    archive_classes=(ZipArchive,), mime_types=('application/zip',)
)
