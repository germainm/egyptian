"""
Pages of an archive (ZIP and JAR, TAR and its compressed forms, 7z, RAR,
ISO, CAB, LHA, AR and DEB, RPM and CPIO, XAR, WARC) and of a single
compressed file (gzip, bzip2, xz, zstd, lzip, lzma, compress): format,
compression, number of entries, sizes, dates, comment, encryption, then
the list of the entries.

Nothing is extracted. ZIP files are read by the zipfile module from their
central directory (archive and entry comments, compression methods, JAR
manifest). The other formats are read by libarchive through libarchive-c,
headers only, with the formats of the MIME type and the built-in
decompression filters enabled, and nothing else: never the mtree format,
whose entries name files of the server, nor the filters that can run an
external program. Reaching the next header of a compressed TAR file means
decompressing the data before it: libarchive reads the file through
read_function, which stops the listing after LISTING_TIME_BUDGET seconds
or DECOMPRESSED_BYTES_MAXIMUM decompressed bytes (decompression bombs).
"""
from datetime import datetime, timezone as datetime_timezone
import ctypes
import logging
import math
import struct
import time

from . import (
    PAGE_ACCENT, PAGE_INK, PAGE_INK_MUTED, PAGE_MARGIN, PAGE_RULE,
    clean_text, draw_fields, font_for, get_font, new_page, wrap_text
)

logger = logging.getLogger(name=__name__)

PAGE_WIDTH = 1600
PAGE_HEIGHT = 2000
NOTE_COLOR = (179, 38, 30)
NOTE_SIZE = 26
FIELD_SIZE = 28
ROW_SIZE = 24
ROW_HEIGHT = 34
FOOTER_HEIGHT = 50

ENTRIES_MAXIMUM = 20000
ENTRIES_SHOWN_MAXIMUM = 2000
LISTING_TIME_BUDGET = 30
DECOMPRESSED_BYTES_MAXIMUM = 4 * 1024 ** 3
READ_BLOCK_SIZE = 16 * 1024
ZIP_ENTRIES_ZIPFILE_MAXIMUM = 100000
MANIFEST_SIZE_MAXIMUM = 64 * 1024
PREVIEW_SIZE = 4096
PREVIEW_LINES_MAXIMUM = 25

ZIP_MIME_TYPES = {
    'application/zip': 'ZIP archive',
    'application/x-zip-compressed': 'ZIP archive',
    'application/java-archive': 'Java archive (JAR)',
    'application/x-java-archive': 'Java archive (JAR)',
    'application/vnd.android.package-archive': 'Android package (APK)',
}
# MIME type: (title, libarchive formats).
LIBARCHIVE_MIME_TYPES = {
    'application/x-tar': ('TAR archive', ('tar',)),
    'application/x-gtar': ('TAR archive', ('tar',)),
    'application/x-ustar': ('TAR archive', ('tar',)),
    'application/x-7z-compressed': ('7-Zip archive', ('7zip',)),
    'application/x-rar': ('RAR archive', ('rar', 'rar5')),
    'application/vnd.rar': ('RAR archive', ('rar', 'rar5')),
    'application/x-rar-compressed': ('RAR archive', ('rar', 'rar5')),
    'application/x-iso9660-image': ('ISO disc image', ('iso9660',)),
    'application/vnd.ms-cab-compressed': ('Cabinet archive (CAB)', ('cab',)),
    'application/x-lzh-compressed': ('LHA archive', ('lha',)),
    'application/x-lha': ('LHA archive', ('lha',)),
    'application/x-archive': ('AR archive', ('ar',)),
    'application/vnd.debian.binary-package': ('Debian package', ('ar',)),
    'application/x-debian-package': ('Debian package', ('ar',)),
    'application/x-rpm': ('RPM package', ('cpio',)),
    'application/x-redhat-package-manager': ('RPM package', ('cpio',)),
    'application/x-cpio': ('CPIO archive', ('cpio',)),
    'application/x-xar': ('XAR archive', ('xar',)),
    'application/warc': ('Web archive (WARC)', ('warc',)),
}
# MIME type of a compressed file: name of its compression. It holds a TAR
# or CPIO archive, or a single file.
COMPRESSED_MIME_TYPES = {
    'application/gzip': 'gzip',
    'application/x-gzip': 'gzip',
    'application/x-bzip2': 'bzip2',
    'application/x-bzip': 'bzip2',
    'application/x-xz': 'xz',
    'application/zstd': 'zstd',
    'application/x-zstd': 'zstd',
    'application/x-lzip': 'lzip',
    'application/x-lzma': 'lzma',
    'application/x-compress': 'compress',
}
ARCHIVE_MIME_TYPES = (
    *ZIP_MIME_TYPES, *LIBARCHIVE_MIME_TYPES, *COMPRESSED_MIME_TYPES
)
# Decompression filters built in libarchive or linked to a library; the
# others (grzip, lrzip, lzop, uu) are left out.
LIBARCHIVE_FILTERS = (
    'bzip2', 'compress', 'gzip', 'lz4', 'lzip', 'lzma', 'rpm', 'xz', 'zstd'
)

ZIP_METHODS = {
    0: 'Stored', 1: 'Shrink', 6: 'Implode', 8: 'Deflate', 9: 'Deflate64',
    12: 'BZIP2', 14: 'LZMA', 93: 'Zstandard', 95: 'XZ', 96: 'JPEG',
    97: 'WavPack', 98: 'PPMd', 99: 'AES'
}
MANIFEST_KEYS = (
    'Implementation-Title', 'Implementation-Version', 'Implementation-Vendor',
    'Bundle-Name', 'Bundle-Version', 'Main-Class', 'Automatic-Module-Name',
    'Created-By'
)
# Pseudo entries: root of an ISO image, symbol and name tables of AR files.
PSEUDO_ENTRIES = ('.', './', '/', '//', '/SYM64/')
GZIP_SYSTEMS = {
    0: 'FAT (MS-DOS, Windows)', 3: 'Unix', 7: 'Macintosh', 11: 'NTFS'
}


class ListingStopped(Exception):
    """The budget of the listing is spent."""


class ArchiveListing:
    def __init__(self, title):
        self.title = title
        self.format = ''
        self.compression = ''
        self.entries = []
        self.entries_read = 0
        self.stop_reason = ''
        self.comment = ''
        self.fields = []
        self.notes = []
        self.encrypted_entries = 0
        self.names_encrypted = False
        self.preview = []
        self.archive_size = None
        self.uncompressed_size = None

    @property
    def complete(self):
        return not self.stop_reason

    def add(self, path, size=None, modified=None, kind='file', link='',
            encrypted=False, comment='', owner=''):
        if path in PSEUDO_ENTRIES:
            return
        self.entries_read += 1
        if encrypted:
            self.encrypted_entries += 1
        self.entries.append(
            {
                'path': path, 'size': size, 'modified': modified,
                'kind': kind, 'link': link, 'encrypted': encrypted,
                'comment': comment, 'owner': owner
            }
        )
        if self.entries_read >= ENTRIES_MAXIMUM:
            raise ListingStopped(
                'more than {:,} entries'.format(ENTRIES_MAXIMUM)
            )

    def reset(self):
        self.entries = []
        self.entries_read = self.encrypted_entries = 0
        self.fields = []


def _file_size(file_object):
    try:
        file_object.seek(0, 2)
        return file_object.tell()
    except (AttributeError, OSError):
        return None
    finally:
        file_object.seek(0)


def _local_time(timestamp):
    """Date of a Unix time, in the time zone of the installation."""
    if not timestamp:
        return None
    try:
        value = datetime.fromtimestamp(timestamp, tz=datetime_timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None
    try:
        from django.utils import timezone

        return timezone.localtime(value)
    except Exception:
        return value


# ZIP, by the zipfile module.

def _zip_entry_count(file_object):
    import zipfile

    try:
        record = zipfile._EndRecData(file_object)
    except Exception:
        return None
    finally:
        file_object.seek(0)
    return record[zipfile._ECD_ENTRIES_TOTAL] if record else None


def _zip_manifest(archive, info):
    """Main fields of the manifest of a JAR file."""
    if info.file_size > MANIFEST_SIZE_MAXIMUM or info.flag_bits & 0x1:
        return []
    with archive.open(info) as member:
        text = member.read(MANIFEST_SIZE_MAXIMUM).decode('utf-8', 'replace')
    values = {}
    key = None
    for line in text.splitlines():
        if line.startswith(' ') and key:
            # A line that starts with a space continues the previous one.
            values[key] += line[1:]
        elif ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            values[key] = value.strip()
        else:
            key = None
    return [
        ('Manifest: {}'.format(key), values[key]) for key in MANIFEST_KEYS
        if values.get(key)
    ]


def _list_zip(file_object, listing):
    import zipfile

    deadline = time.monotonic() + LISTING_TIME_BUDGET
    file_object.seek(0)
    with zipfile.ZipFile(file_object) as archive:
        listing.format = 'ZIP'
        listing.comment = archive.comment.decode('utf-8', 'replace')
        methods = {}
        for info in archive.infolist():
            if time.monotonic() > deadline:
                raise ListingStopped('time limit')
            mode = info.external_attr >> 16
            if info.is_dir():
                kind = 'directory'
            elif info.create_system == 3 and mode & 0o170000 == 0o120000:
                kind = 'link'
            else:
                kind = 'file'
                method = ZIP_METHODS.get(
                    info.compress_type, 'method {}'.format(info.compress_type)
                )
                methods[method] = methods.get(method, 0) + 1
            try:
                modified = datetime(*info.date_time)
            except ValueError:
                modified = None
            if info.filename == 'META-INF/MANIFEST.MF':
                try:
                    listing.fields.extend(
                        _zip_manifest(archive=archive, info=info)
                    )
                except Exception as exception:
                    logger.debug('JAR manifest not read; %s', exception)
            try:
                listing.add(
                    path=info.filename, size=info.file_size,
                    modified=modified, kind=kind,
                    encrypted=bool(info.flag_bits & 0x1),
                    comment=info.comment.decode('utf-8', 'replace')
                )
            finally:
                listing.compression = ', '.join(
                    '{} ({:,})'.format(method, count) if len(methods) > 1
                    else method for method, count in sorted(
                        methods.items(), key=lambda item: -item[1]
                    )
                )


# Other formats, by libarchive.

SKIP_CALLBACK = ctypes.CFUNCTYPE(
    ctypes.c_longlong, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_longlong
)


def _library_function(name, restype, argtypes):
    from libarchive import ffi

    function = getattr(ffi.libarchive, name, None)
    if function is not None:
        function.restype = restype
        function.argtypes = argtypes
    return function


class LibarchiveReader:
    """
    A libarchive reader of the file object, limited to some formats and
    filters, that stops when its budget is spent.
    """
    def __init__(self, file_object, formats, filters):
        self.file_object = file_object
        self.formats = formats
        self.filters = filters
        self.deadline = time.monotonic() + LISTING_TIME_BUDGET
        self.stop_reason = ''
        self.size = _file_size(file_object=file_object)
        self.block = None

    def over_budget(self):
        if time.monotonic() > self.deadline:
            self.stop_reason = 'time limit'
        elif self.filter_bytes and self.filter_bytes(
            self.archive_p, 0
        ) > DECOMPRESSED_BYTES_MAXIMUM:
            self.stop_reason = '{} decompressed'.format(
                format_size(DECOMPRESSED_BYTES_MAXIMUM)
            )
        return bool(self.stop_reason)

    def _read(self, archive_p, context, pointer_pointer):
        if self.over_budget():
            return -1
        data = self.file_object.read(READ_BLOCK_SIZE)
        ctypes.memmove(self.buffer, data, len(data))
        ctypes.cast(
            pointer_pointer, ctypes.POINTER(ctypes.c_void_p)
        )[0] = ctypes.cast(self.buffer, ctypes.c_void_p)
        return len(data)

    def _seek(self, archive_p, context, offset, whence):
        self.file_object.seek(offset, whence)
        return self.file_object.tell()

    def _skip(self, archive_p, context, request):
        # Skipped data that is not decompressed: a seek.
        if self.over_budget() or self.size is None:
            return 0
        position = self.file_object.tell()
        skipped = max(0, min(request, self.size - position))
        self.file_object.seek(position + skipped)
        return skipped

    def __enter__(self):
        from libarchive import ffi
        from libarchive.read import ArchiveRead

        self.buffer = ctypes.create_string_buffer(READ_BLOCK_SIZE)
        self.filter_bytes = _library_function(
            name='archive_filter_bytes', restype=ctypes.c_longlong,
            argtypes=(ctypes.c_void_p, ctypes.c_int)
        )
        self.archive_p = ffi.read_new()
        # Kept: libarchive calls them until read_free.
        self.callbacks = (
            ffi.READ_CALLBACK(self._read), ffi.SEEK_CALLBACK(self._seek),
            SKIP_CALLBACK(self._skip)
        )
        try:
            for name in self.formats:
                ffi.get_read_format_function(name)(self.archive_p)
            for name in self.filters:
                try:
                    ffi.get_read_filter_function(name)(self.archive_p)
                except Exception as exception:
                    logger.debug(
                        'libarchive filter %s unavailable; %s', name, exception
                    )
            ffi.read_set_seek_callback(self.archive_p, self.callbacks[1])
            set_skip_callback = _library_function(
                name='archive_read_set_skip_callback', restype=ctypes.c_int,
                argtypes=(ctypes.c_void_p, SKIP_CALLBACK)
            )
            if set_skip_callback:
                set_skip_callback(self.archive_p, self.callbacks[2])
            self.file_object.seek(0)
            ffi.read_open(
                self.archive_p, None, ffi.NO_OPEN_CB, self.callbacks[0],
                ffi.NO_CLOSE_CB
            )
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return ArchiveRead(self.archive_p)

    def __exit__(self, *args):
        from libarchive import ffi

        ffi.read_free(self.archive_p)
        self.file_object.seek(0)

    def is_compressed(self):
        from libarchive import ffi

        return ffi.filter_count(self.archive_p) > 1

    def consume_data(self):
        """
        Read the data of the current entry by blocks that are not kept,
        checking the budget after each one. libarchive would otherwise
        decompress it in one go to reach the next header: a few bytes of
        bzip2 can hold gigabytes of zeros, decompressed with no read of
        the file, so with no call to _read.
        """
        from libarchive import ffi

        if self.block is None:
            self.block = ctypes.create_string_buffer(1024 * 1024)
        while True:
            if self.over_budget():
                raise ListingStopped(self.stop_reason)
            if ffi.read_data(self.archive_p, self.block, len(self.block)) <= 0:
                return

    def describe(self, listing):
        from libarchive import ffi

        name = ffi.format_name(self.archive_p)
        if name:
            listing.format = name.decode('utf-8', 'replace')
        filters = []
        for index in range(ffi.filter_count(self.archive_p)):
            name = ffi.filter_name(self.archive_p, index)
            name = name.decode('utf-8', 'replace') if name else ''
            if name and name != 'none':
                filters.append(name)
        listing.compression = ', '.join(filters)


def _entry_path(entry):
    try:
        return entry.pathname or ''
    except Exception:
        return '(name not readable)'


def _list_libarchive(file_object, listing, formats):
    is_encrypted = _library_function(
        name='archive_entry_is_data_encrypted', restype=ctypes.c_int,
        argtypes=(ctypes.c_void_p,)
    )
    owners = {}
    reader = LibarchiveReader(
        file_object=file_object, formats=formats, filters=LIBARCHIVE_FILTERS
    )
    try:
        with reader as archive:
            consume = None
            try:
                for entry in archive:
                    if consume is None:
                        consume = reader.is_compressed() and set(formats) & {
                            'tar', 'cpio'
                        }
                    if entry.isdir:
                        kind = 'directory'
                    elif entry.issym or entry.islnk:
                        kind = 'link'
                    elif entry.isreg:
                        kind = 'file'
                    else:
                        kind = 'other'
                    owner = '/'.join(
                        name for name in (entry.uname, entry.gname) if name
                    )
                    if owner:
                        owners[owner] = owners.get(owner, 0) + 1
                    listing.add(
                        path=_entry_path(entry=entry),
                        size=entry.size if kind == 'file' else None,
                        modified=_local_time(entry.mtime), kind=kind,
                        link=entry.linkpath or '', encrypted=bool(
                            is_encrypted and is_encrypted(entry._entry_p) > 0
                        ), owner=owner
                    )
                    # Compressed TAR or CPIO stream: the data before the
                    # next header must be decompressed. 7z, RAR, CAB and
                    # LHA skip the data of an entry without decompressing
                    # it, or read their compressed data as they go.
                    if kind == 'file' and entry.size and consume:
                        reader.consume_data()
            except ListingStopped:
                raise
            except Exception as exception:
                if reader.stop_reason:
                    raise ListingStopped(reader.stop_reason)
                message = error_message(exception=exception)
                if not listing.entries_read and (
                    'ncrypt' in message or 'assphrase' in message
                ):
                    listing.names_encrypted = True
                elif listing.entries_read:
                    raise ListingStopped(
                        'read error: {}'.format(
                            clean_text(message, maximum_length=200)
                        )
                    )
                else:
                    raise
            finally:
                reader.describe(listing=listing)
    finally:
        if owners:
            listing.fields.append(
                (
                    'Owners', ', '.join(
                        '{} ({:,})'.format(owner, count)
                        for owner, count in sorted(
                            owners.items(), key=lambda item: -item[1]
                        )[:6]
                    )
                )
            )


def error_message(exception):
    """Message of the exception, without the libarchive-c details."""
    return str(getattr(exception, 'msg', '') or exception)


def _gzip_header(file_object):
    """Original name, comment, date and system of a gzip file."""
    file_object.seek(0)
    head = file_object.read(64 * 1024)
    file_object.seek(0)
    if len(head) < 10 or head[:2] != b'\x1f\x8b':
        return []
    flags = head[3]
    fields = []
    position = 10
    try:
        if flags & 0x04:
            position += 2 + struct.unpack('<H', head[10:12])[0]
        if flags & 0x08:
            end = head.index(b'\x00', position)
            fields.append(('Original name', head[position:end].decode('latin-1')))
            position = end + 1
        if flags & 0x10:
            end = head.index(b'\x00', position)
            fields.append(('Comment', head[position:end].decode('latin-1')))
    except (ValueError, struct.error):
        pass
    compressed_on = _local_time(struct.unpack('<I', head[4:8])[0])
    if compressed_on:
        fields.append(
            ('Compressed on', compressed_on.strftime('%Y-%m-%d %H:%M'))
        )
    if head[9] in GZIP_SYSTEMS:
        fields.append(('System', GZIP_SYSTEMS[head[9]]))
    return fields


def _text_preview(data):
    """First lines of the data when it is text, else nothing."""
    if not data or b'\x00' in data:
        return []
    text = data.decode('utf-8', 'replace')
    if text.count('�') > len(text) / 50:
        return []
    printable = sum(
        1 for character in text
        if character.isprintable() or character in '\t\r\n'
    )
    if printable < len(text) * 0.95:
        return []
    lines = text.splitlines()
    if len(data) >= PREVIEW_SIZE and len(lines) > 1:
        # The last line may be cut.
        lines = lines[:-1]
    return lines[:PREVIEW_LINES_MAXIMUM]


def _list_compressed_file(file_object, listing, compression):
    """A compressed file that holds no archive: its size and its start."""
    from libarchive import ffi

    listing.format = 'Compressed file'
    listing.compression = compression
    if compression == 'gzip':
        listing.fields.extend(_gzip_header(file_object=file_object))
    reader = LibarchiveReader(
        file_object=file_object, formats=('raw',), filters=LIBARCHIVE_FILTERS
    )
    with reader as archive:
        for entry in archive:
            # Decompressed to measure it, by blocks that are not kept but
            # the first bytes.
            block = ctypes.create_string_buffer(1024 * 1024)
            head = b''
            total = 0
            stopped = ''
            while True:
                if total > DECOMPRESSED_BYTES_MAXIMUM:
                    stopped = '{} decompressed'.format(
                        format_size(DECOMPRESSED_BYTES_MAXIMUM)
                    )
                    break
                if time.monotonic() > reader.deadline:
                    stopped = 'time limit'
                    break
                try:
                    length = ffi.read_data(reader.archive_p, block, len(block))
                except Exception as exception:
                    stopped = reader.stop_reason or 'read error: {}'.format(
                        error_message(exception=exception)
                    )
                    break
                if length <= 0:
                    break
                if len(head) < PREVIEW_SIZE:
                    head += ctypes.string_at(
                        block, min(length, PREVIEW_SIZE - len(head))
                    )
                total += length
            listing.preview = _text_preview(data=head)
            if stopped:
                listing.fields.append(
                    (
                        'Uncompressed size', 'more than {} (measure '
                        'stopped: {})'.format(format_size(total), stopped)
                    )
                )
            else:
                listing.uncompressed_size = total
            break


def list_archive(file_object, mime_type):
    if mime_type in ZIP_MIME_TYPES:
        listing = ArchiveListing(title=ZIP_MIME_TYPES[mime_type])
    elif mime_type in LIBARCHIVE_MIME_TYPES:
        listing = ArchiveListing(title=LIBARCHIVE_MIME_TYPES[mime_type][0])
    else:
        listing = ArchiveListing(
            title='Compressed file ({})'.format(COMPRESSED_MIME_TYPES[mime_type])
        )
    listing.archive_size = _file_size(file_object=file_object)
    try:
        import libarchive  # NOQA: F401
    except (ImportError, OSError):
        libarchive_installed = False
    else:
        libarchive_installed = True

    try:
        if mime_type in ZIP_MIME_TYPES:
            count = _zip_entry_count(file_object=file_object)
            if libarchive_installed and (
                count is None or count > ZIP_ENTRIES_ZIPFILE_MAXIMUM
            ):
                # Huge or damaged: libarchive reads the entries one by one.
                _list_libarchive(
                    file_object=file_object, listing=listing, formats=('zip',)
                )
            else:
                _list_zip(file_object=file_object, listing=listing)
        elif not libarchive_installed:
            listing.notes.append(
                'The content is not listed: install the libarchive-c Python '
                'package (and the libarchive library) to list the {} '
                'files.'.format(listing.title)
            )
        elif mime_type in LIBARCHIVE_MIME_TYPES:
            _list_libarchive(
                file_object=file_object, listing=listing,
                formats=LIBARCHIVE_MIME_TYPES[mime_type][1]
            )
        else:
            compression = COMPRESSED_MIME_TYPES[mime_type]
            try:
                _list_libarchive(
                    file_object=file_object, listing=listing,
                    formats=('tar', 'cpio')
                )
            except ListingStopped:
                if listing.entries_read:
                    listing.title = 'TAR archive ({})'.format(compression)
                raise
            except Exception as exception:
                if 'nrecognized archive format' not in error_message(
                    exception=exception
                ):
                    raise
                is_archive = False
            else:
                # 512 zero bytes end a TAR archive: a compressed file that
                # starts with them is read as an empty TAR archive.
                is_archive = bool(listing.entries_read)
            if not is_archive:
                listing.reset()
                _list_compressed_file(
                    file_object=file_object, listing=listing,
                    compression=compression
                )
            else:
                listing.title = 'TAR archive ({})'.format(compression)
                if listing.format and 'cpio' in listing.format.lower():
                    listing.title = 'CPIO archive ({})'.format(compression)
    except ListingStopped as exception:
        listing.stop_reason = str(exception)
    except Exception as exception:
        logger.warning('Archive not listed; %s', exception)
        listing.notes.append(
            'The archive could not be read: {}'.format(
                clean_text(
                    error_message(exception=exception), maximum_length=300
                )
            )
        )
    finally:
        file_object.seek(0)

    if listing.names_encrypted:
        listing.notes.append(
            'The names of the entries are encrypted: the content of the '
            'archive cannot be listed without its password.'
        )
    if not listing.complete:
        listing.notes.append(
            'Listing stopped after {} ({}).'.format(
                _count(listing.entries_read, 'entry', 'entries'),
                listing.stop_reason
            )
        )
    if len(listing.entries) > ENTRIES_SHOWN_MAXIMUM:
        listing.notes.append(
            'Only the first {:,} entries are listed on the pages.'.format(
                ENTRIES_SHOWN_MAXIMUM
            )
        )
    return listing


# Pages.

def format_size(size):
    if size is None:
        return ''
    value = float(size)
    for unit in ('B', 'KB', 'MB', 'GB'):
        if value < 1024:
            return '{} B'.format(int(value)) if unit == 'B' else '{:.1f} {}'.format(value, unit)
        value /= 1024
    return '{:.1f} TB'.format(value)


def _count(number, singular, plural):
    return '{:,} {}'.format(number, singular if number == 1 else plural)


def summary_fields(listing):
    files = [entry for entry in listing.entries if entry['kind'] == 'file']
    directories = sum(
        1 for entry in listing.entries if entry['kind'] == 'directory'
    )
    others = len(listing.entries) - len(files) - directories
    fields = []
    if listing.format:
        fields.append(('Format', listing.format))
    if listing.compression:
        fields.append(('Compression', listing.compression))
    if listing.entries:
        counts = [_count(len(files), 'file', 'files')]
        if directories:
            counts.append(_count(directories, 'folder', 'folders'))
        if others:
            counts.append(_count(others, 'link or other', 'links and others'))
        fields.append(('Entries', ', '.join(counts)))
    total = listing.uncompressed_size
    if total is None and files:
        total = sum(entry['size'] or 0 for entry in files)
    sizes = []
    if total is not None:
        sizes.append('{} uncompressed'.format(format_size(total)))
    if listing.archive_size is not None:
        sizes.append('file {}'.format(format_size(listing.archive_size)))
        if total and listing.archive_size < total:
            ratio = listing.archive_size / total
            sizes.append(
                'compressed to {}'.format(
                    'less than 1%' if ratio < 0.01 else '{:.0%}'.format(ratio)
                )
            )
    if sizes:
        fields.append(('Size', ', '.join(sizes)))
    dates = [entry['modified'] for entry in listing.entries if entry['modified']]
    if dates:
        oldest, newest = min(dates), max(dates)
        text = oldest.strftime('%Y-%m-%d %H:%M')
        if newest != oldest:
            text += ' – ' + newest.strftime('%Y-%m-%d %H:%M')
        fields.append(('Dates', text))
    if listing.encrypted_entries:
        fields.append(
            (
                'Encryption', '{:,} of {} encrypted (password needed to '
                'open them)'.format(
                    listing.encrypted_entries,
                    _count(listing.entries_read, 'entry', 'entries')
                )
            )
        )
    elif listing.names_encrypted:
        fields.append(('Encryption', 'names and content encrypted'))
    fields.extend(listing.fields)
    if listing.comment:
        fields.append(('Comment', listing.comment))
    return fields


def _fit(draw, text, font, width):
    """The text, cut in its middle with … when wider than width."""
    if draw.textlength(text, font=font) <= width:
        return text
    head = tail = len(text) // 2
    while head + tail > 2 and draw.textlength(
        text[:head] + '…' + text[len(text) - tail:], font=font
    ) > width:
        if head > tail:
            head -= 1
        else:
            tail -= 1
    return text[:head] + '…' + text[len(text) - tail:]


class ArchiveLayout:
    """Pages of the listing: summary, then the entries in a table."""
    def __init__(self, listing):
        self.listing = listing
        self.shown = listing.entries[:ENTRIES_SHOWN_MAXIMUM]
        self.content_width = PAGE_WIDTH - 2 * PAGE_MARGIN
        image, draw = new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        self.header_bottom = self._draw_header(draw=draw)
        del draw
        rows_bottom = PAGE_HEIGHT - PAGE_MARGIN - FOOTER_HEIGHT
        # Page 1: the rows below the summary, if a table header and two
        # rows fit; the next pages: below their title.
        self.first_rows = max(
            0, (rows_bottom - self.header_bottom - 30) // ROW_HEIGHT - 1
        )
        if self.first_rows < 2:
            self.first_rows = 0
        self.rows_per_page = (
            rows_bottom - (PAGE_MARGIN + 70)
        ) // ROW_HEIGHT - 1

    @property
    def page_count(self):
        remaining = len(self.shown) - self.first_rows
        if remaining <= 0:
            return 1
        return 1 + math.ceil(remaining / self.rows_per_page)

    def _rows(self, page_number):
        if page_number == 0:
            return 0, self.shown[:self.first_rows]
        start = self.first_rows + (page_number - 1) * self.rows_per_page
        return start, self.shown[start:start + self.rows_per_page]

    def _draw_header(self, draw):
        """Title, notes, summary and start of a compressed file; its bottom."""
        draw.text(
            xy=(PAGE_MARGIN, PAGE_MARGIN - 10), text=self.listing.title,
            font=get_font(size=46, style='bold'), fill=PAGE_INK
        )
        y = PAGE_MARGIN + 66
        font_note = get_font(size=NOTE_SIZE, style='bold')
        for note in self.listing.notes:
            for line in wrap_text(
                draw=draw, text=clean_text(note, maximum_length=600),
                font=font_note, width=self.content_width, maximum_lines=4
            ):
                draw.text(
                    xy=(PAGE_MARGIN, y), text=line, font=font_note,
                    fill=NOTE_COLOR
                )
                y += int(NOTE_SIZE * 1.3)
            y += 8
        y = draw_fields(
            draw=draw, xy=(PAGE_MARGIN, y + 10),
            fields=summary_fields(listing=self.listing),
            width=self.content_width, size=FIELD_SIZE
        )
        if self.listing.preview:
            y += 16
            draw.text(
                xy=(PAGE_MARGIN, y), text='Beginning of the content',
                font=get_font(size=FIELD_SIZE, style='bold'), fill=PAGE_ACCENT
            )
            y += 48
            for line in self.listing.preview:
                if y > PAGE_HEIGHT - PAGE_MARGIN - 40:
                    break
                line = clean_text(line.expandtabs(4))
                font_line = font_for(text=line, size=22, style='mono')
                draw.text(
                    xy=(PAGE_MARGIN, y), text=_fit(
                        draw=draw, text=line, font=font_line,
                        width=self.content_width
                    ), font=font_line, fill=PAGE_INK
                )
                y += 30
        return y

    def _draw_rows(self, draw, y, rows):
        size_width, date_width = 160, 230
        name_width = self.content_width - size_width - date_width - 50
        x_size = PAGE_MARGIN + name_width + 20 + size_width
        x_date = PAGE_MARGIN + self.content_width - date_width
        font = get_font(size=ROW_SIZE)
        font_bold = get_font(size=ROW_SIZE, style='bold')
        for label, x, anchor in (
            ('Name', PAGE_MARGIN, 'la'), ('Size', x_size, 'ra'),
            ('Modified', x_date, 'la')
        ):
            draw.text(
                xy=(x, y), text=label, font=font_bold, fill=PAGE_INK_MUTED,
                anchor=anchor
            )
        y += ROW_HEIGHT
        draw.line(
            xy=(PAGE_MARGIN, y - 6, PAGE_MARGIN + self.content_width, y - 6),
            fill=PAGE_RULE, width=2
        )
        for entry in rows:
            name = clean_text(entry['path'], maximum_length=1000)
            if entry['kind'] == 'directory' and not name.endswith('/'):
                name += '/'
            if entry['link']:
                name += ' → ' + clean_text(entry['link'], maximum_length=300)
            tags = []
            if entry['encrypted']:
                tags.append('encrypted')
            if entry['comment']:
                tags.append(clean_text(entry['comment'], maximum_length=200))
            if tags:
                name += ' [{}]'.format('; '.join(tags))
            font_name = font_for(text=name, size=ROW_SIZE)
            draw.text(
                xy=(PAGE_MARGIN, y), text=_fit(
                    draw=draw, text=name, font=font_name, width=name_width
                ), font=font_name, fill=PAGE_INK_MUTED
                if entry['kind'] == 'directory' else PAGE_INK
            )
            if entry['kind'] == 'file' and entry['size'] is not None:
                draw.text(
                    xy=(x_size, y), text=format_size(entry['size']),
                    font=font, fill=PAGE_INK, anchor='ra'
                )
            if entry['modified']:
                draw.text(
                    xy=(x_date, y),
                    text=entry['modified'].strftime('%Y-%m-%d %H:%M'),
                    font=font, fill=PAGE_INK_MUTED
                )
            y += ROW_HEIGHT

    def render(self, page_number):
        page_number = max(0, min(page_number, self.page_count - 1))
        start, rows = self._rows(page_number=page_number)
        image, draw = new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        if page_number == 0:
            y = self._draw_header(draw=draw) + 30
        else:
            draw.text(
                xy=(PAGE_MARGIN, PAGE_MARGIN - 10),
                text='{} (continued)'.format(self.listing.title),
                font=get_font(size=34, style='bold'), fill=PAGE_INK
            )
            y = PAGE_MARGIN + 70
        if rows:
            self._draw_rows(draw=draw, y=y, rows=rows)
        if self.shown:
            footer = []
            if rows:
                footer.append(
                    'Entries {:,}–{:,} of {:,}{}'.format(
                        start + 1, start + len(rows), self.listing.entries_read,
                        '' if self.listing.complete else ' (listing incomplete)'
                    )
                )
            footer.append('page {} of {}'.format(page_number + 1, self.page_count))
            draw.text(
                xy=(PAGE_MARGIN, PAGE_HEIGHT - PAGE_MARGIN),
                text=' · '.join(footer), font=get_font(size=22),
                fill=PAGE_INK_MUTED, anchor='ls'
            )
        del draw
        return image

    def text(self, page_number):
        """Text of the page, for the search."""
        page_number = max(0, min(page_number, self.page_count - 1))
        start, rows = self._rows(page_number=page_number)
        lines = []
        if page_number == 0:
            lines.append(self.listing.title)
            lines.extend(self.listing.notes)
            lines.extend(
                '{}: {}'.format(label, value)
                for label, value in summary_fields(listing=self.listing)
            )
            lines.extend(self.listing.preview)
        if page_number == self.page_count - 1:
            # The entries read but not shown on the pages are searchable.
            rows = rows + self.listing.entries[len(self.shown):]
        for entry in rows:
            columns = [entry['path']]
            if entry['link']:
                columns[0] += ' -> ' + entry['link']
            if entry['kind'] == 'file' and entry['size'] is not None:
                columns.append(format_size(entry['size']))
            if entry['modified']:
                columns.append(entry['modified'].strftime('%Y-%m-%d %H:%M'))
            if entry['comment']:
                columns.append(entry['comment'])
            lines.append('\t'.join(columns))
        return '\n'.join(lines)


def get_archive_layout(file_object, mime_type):
    return ArchiveLayout(
        listing=list_archive(file_object=file_object, mime_type=mime_type)
    )
