"""
Information that libarchive does not give: the header of an RPM package
(name, version, summary, license, vendor, build date, signature…) and the
properties of a RAR archive (solid, locked, recovery record, volume,
compression method, system, comment). Read from the first bytes of the
file only, every length checked against the data read.
"""
from datetime import datetime, timezone as datetime_timezone
import struct
import zlib

HEAD_SIZE_MAXIMUM = 4 * 1024 * 1024
RAR_HEADERS_MAXIMUM = 64
RAR_COMMENT_MAXIMUM = 64 * 1024
RPM_INDEX_MAXIMUM = 65536
RPM_DESCRIPTION_MAXIMUM = 600

RPM_LEAD_MAGIC = b'\xed\xab\xee\xdb'
RPM_HEADER_MAGIC = b'\x8e\xad\xe8\x01'
RPM_LEAD_SIZE = 96
RPM_TYPE_INT32 = 4
RPM_TYPE_STRING = 6
RPM_TYPE_STRING_ARRAY = 8
RPM_TYPE_I18NSTRING = 9
# Signature header tags of the OpenPGP signatures (DSA, RSA, PGP, GPG,
# OpenPGP of rpm 6).
RPM_SIGNATURE_TAGS = {267, 268, 278, 1002, 1005}
RPM_TAGS = {
    1000: 'name', 1001: 'version', 1002: 'release', 1004: 'summary',
    1005: 'description', 1006: 'build_time', 1007: 'build_host',
    1009: 'size', 1010: 'distribution', 1011: 'vendor', 1014: 'license',
    1015: 'packager', 1016: 'group', 1020: 'url', 1022: 'arch',
    1044: 'source_rpm', 1124: 'payload_format', 1125: 'payload_compressor',
    5009: 'long_size'
}

RAR4_SIGNATURE = b'Rar!\x1a\x07\x00'
RAR5_SIGNATURE = b'Rar!\x1a\x07\x01\x00'
RAR_SYSTEMS = {
    4: {0: 'MS-DOS', 1: 'OS/2', 2: 'Windows', 3: 'Unix', 4: 'Mac OS', 5: 'BeOS'},
    5: {0: 'Windows', 1: 'Unix'}
}
RAR_METHODS = ('Store', 'Fastest', 'Fast', 'Normal', 'Good', 'Best')


def _read_head(file_object, size=HEAD_SIZE_MAXIMUM):
    file_object.seek(0)
    try:
        return file_object.read(size)
    finally:
        file_object.seek(0)


def _format_size(size):
    from .archive import format_size

    return format_size(size)


# RPM.

def _rpm_header(data, position):
    """Index and store of an RPM header structure; its end."""
    if position + 16 > len(data):
        raise ValueError('RPM header truncated')
    if data[position:position + 4] != RPM_HEADER_MAGIC:
        raise ValueError('RPM header not found')
    count, store_size = struct.unpack_from('>II', data, position + 8)
    if count > RPM_INDEX_MAXIMUM:
        raise ValueError('RPM header too large')
    index_start = position + 16
    store_start = index_start + 16 * count
    store_end = store_start + store_size
    if store_end > len(data):
        raise ValueError('RPM header truncated')
    entries = {}
    for number in range(count):
        tag, kind, offset, item_count = struct.unpack_from(
            '>iiii', data, index_start + 16 * number
        )
        if 0 <= offset < store_size:
            entries[tag] = (kind, store_start + offset, item_count)
    return entries, store_end


def _rpm_value(data, entry, store_end):
    kind, offset, count = entry
    if kind in (RPM_TYPE_STRING, RPM_TYPE_STRING_ARRAY, RPM_TYPE_I18NSTRING):
        # The first string of an array: the untranslated one.
        end = data.find(b'\x00', offset, store_end)
        if end < 0:
            return None
        return data[offset:end].decode('utf-8', 'replace')
    if kind == RPM_TYPE_INT32 and offset + 4 <= store_end:
        return struct.unpack_from('>I', data, offset)[0]
    return None


def get_rpm_fields(file_object):
    """(leading fields, other fields) of the header of an RPM package."""
    data = _read_head(file_object=file_object)
    if data[:4] != RPM_LEAD_MAGIC:
        return [], []
    signature, end = _rpm_header(data=data, position=RPM_LEAD_SIZE)
    # The main header starts on the next multiple of 8 bytes.
    position = end + (-(end - RPM_LEAD_SIZE) % 8)
    entries, store_end = _rpm_header(data=data, position=position)
    values = {}
    for tag, name in RPM_TAGS.items():
        if tag in entries:
            values[name] = _rpm_value(
                data=data, entry=entries[tag], store_end=store_end
            )
    package = '-'.join(
        str(values[name]) for name in ('name', 'version', 'release')
        if values.get(name)
    )
    if package and values.get('arch'):
        package += '.{}'.format(values['arch'])
    leading = []
    if package:
        leading.append(('Package', package))
    if values.get('summary'):
        leading.append(('Summary', values['summary']))
    fields = []
    for label, name in (
        ('License', 'license'), ('Vendor', 'vendor'),
        ('Packager', 'packager'), ('Distribution', 'distribution'),
        ('Group', 'group'), ('URL', 'url'), ('Source package', 'source_rpm')
    ):
        if values.get(name) and values[name] != 'Unspecified':
            fields.append((label, values[name]))
    if values.get('build_time'):
        build = datetime.fromtimestamp(
            values['build_time'], tz=datetime_timezone.utc
        ).strftime('%Y-%m-%d %H:%M UTC')
        if values.get('build_host'):
            build += ' on {}'.format(values['build_host'])
        fields.append(('Built', build))
    size = values.get('long_size') or values.get('size')
    if size:
        fields.append(('Installed size', _format_size(size)))
    if values.get('payload_format'):
        payload = values['payload_format']
        if values.get('payload_compressor'):
            payload += ', {}'.format(values['payload_compressor'])
        fields.append(('Payload', payload))
    fields.append(
        (
            'Signature', 'OpenPGP signature present (not verified)'
            if RPM_SIGNATURE_TAGS & set(signature) else 'none'
        )
    )
    if values.get('description'):
        description = ' '.join(values['description'].split())
        if len(description) > RPM_DESCRIPTION_MAXIMUM:
            description = description[:RPM_DESCRIPTION_MAXIMUM - 1] + '…'
        fields.append(('Description', description))
    return leading, fields


# RAR.

def _vint(data, position):
    """Variable length integer of RAR 5; its value and the next position."""
    value = shift = 0
    for index in range(10):
        if position + index >= len(data):
            raise ValueError('RAR header truncated')
        byte = data[position + index]
        value |= (byte & 0x7f) << shift
        if not byte & 0x80:
            return value, position + index + 1
        shift += 7
    raise ValueError('RAR vint too long')


def _rar5_properties(data):
    info = {'flags': [], 'comment': None}
    position = len(RAR5_SIGNATURE)
    for _ in range(RAR_HEADERS_MAXIMUM):
        if position + 4 > len(data):
            break
        crc = struct.unpack_from('<I', data, position)[0]
        size, start = _vint(data, position + 4)
        end = start + size
        if size > HEAD_SIZE_MAXIMUM or end > len(data):
            break
        if zlib.crc32(data[position + 4:end]) != crc:
            info['flags'].append('damaged header')
            break
        kind, cursor = _vint(data, start)
        flags, cursor = _vint(data, cursor)
        extra_size = data_size = 0
        if flags & 0x0001:
            extra_size, cursor = _vint(data, cursor)
        if flags & 0x0002:
            data_size, cursor = _vint(data, cursor)
        if kind == 4:
            # Archive encryption header: the next headers are encrypted.
            info['headers_encrypted'] = True
            break
        if kind == 1:
            archive_flags, cursor = _vint(data, cursor)
            if archive_flags & 0x0001:
                volume = 1
                if archive_flags & 0x0002:
                    volume, cursor = _vint(data, cursor)
                    volume += 1
                info['flags'].append('volume {} of a set'.format(volume))
            for bit, label in (
                (0x0004, 'solid'), (0x0008, 'recovery record'),
                (0x0010, 'locked')
            ):
                if archive_flags & bit:
                    info['flags'].append(label)
        elif kind in (2, 3):
            file_flags, cursor = _vint(data, cursor)
            _, cursor = _vint(data, cursor)  # Unpacked size.
            _, cursor = _vint(data, cursor)  # Attributes.
            if file_flags & 0x0002:
                cursor += 4
            if file_flags & 0x0004:
                cursor += 4
            compression, cursor = _vint(data, cursor)
            system, cursor = _vint(data, cursor)
            name_length, cursor = _vint(data, cursor)
            name = data[cursor:cursor + name_length].decode('utf-8', 'replace')
            extra_start = end - extra_size
            encrypted = _rar5_extra_has_record(
                data=data, start=extra_start, end=end, record_type=0x01
            )
            # The method of the first file; a folder has none.
            if kind == 2 and 'method' not in info and not file_flags & 0x0001:
                method = (compression >> 7) & 0x07
                info['method'] = RAR_METHODS[method] if method < len(RAR_METHODS) else str(method)
                if method:
                    info['dictionary'] = 128 * 1024 << ((compression >> 10) & 0x1f)
                info['system'] = RAR_SYSTEMS[5].get(system)
            if kind == 3 and name == 'CMT':
                info['comment'] = _rar5_comment(
                    data=data, start=end, size=data_size,
                    method=(compression >> 7) & 0x07, encrypted=encrypted
                )
        elif kind == 5:
            break
        position = end + data_size
    return info


def _rar5_extra_records(data, start, end):
    """Records of the extra area of a RAR 5 header: {type: data start}."""
    records = {}
    cursor = start
    while cursor < end:
        size, after = _vint(data, cursor)
        if not size:
            break
        kind, data_start = _vint(data, after)
        records.setdefault(kind, data_start)
        cursor = after + size
    return records


def _rar5_extra_has_record(data, start, end, record_type):
    return record_type in _rar5_extra_records(data=data, start=start, end=end)


def _rar5_comment(data, start, size, method, encrypted):
    if encrypted:
        return 'present (encrypted)'
    if method:
        return 'present (compressed, not shown)'
    if size > RAR_COMMENT_MAXIMUM or start + size > len(data):
        return 'present (too long to be shown)'
    return data[start:start + size].decode('utf-8', 'replace').strip(' \t\r\n\x00')


def _rar4_properties(data):
    info = {'flags': [], 'comment': None}
    position = len(RAR4_SIGNATURE)
    for _ in range(RAR_HEADERS_MAXIMUM):
        if position + 7 > len(data):
            break
        _, kind, flags, size = struct.unpack_from('<HBHH', data, position)
        if size < 7:
            break
        add_size = 0
        if flags & 0x8000 and position + 11 <= len(data):
            add_size = struct.unpack_from('<I', data, position + 7)[0]
        if kind == 0x73:
            for bit, label in (
                (0x0001, 'volume of a set'), (0x0008, 'solid'),
                (0x0040, 'recovery record'), (0x0004, 'locked')
            ):
                if flags & bit:
                    info['flags'].append(label)
            if flags & 0x0002:
                info['comment'] = 'present (compressed, not shown)'
            if flags & 0x0080:
                # Encrypted headers: nothing more can be read.
                info['headers_encrypted'] = True
                break
        elif kind in (0x74, 0x7a) and position + 32 <= len(data):
            system = data[position + 15]
            method = data[position + 25] - 0x30
            name_size = struct.unpack_from('<H', data, position + 26)[0]
            name_start = position + 32 + (8 if flags & 0x0100 else 0)
            name = data[name_start:name_start + name_size]
            is_directory = flags & 0x00e0 == 0x00e0
            if kind == 0x74 and 'method' not in info and not is_directory:
                info['method'] = RAR_METHODS[method] if 0 <= method < len(RAR_METHODS) else str(method)
                info['system'] = RAR_SYSTEMS[4].get(system)
                info['version'] = data[position + 24]
            if kind == 0x7a and name == b'CMT':
                info['comment'] = 'present (compressed, not shown)' if method else (
                    data[position + size:position + size + min(add_size, RAR_COMMENT_MAXIMUM)]
                    .decode('utf-8', 'replace').strip(' \t\r\n\x00')
                )
        elif kind == 0x7b:
            break
        position += size + add_size
    return info


def get_rar_fields(file_object):
    """Fields of the properties of a RAR archive."""
    data = _read_head(file_object=file_object)
    if data.startswith(RAR5_SIGNATURE):
        info = _rar5_properties(data=data)
        version = 'RAR 5'
    elif data.startswith(RAR4_SIGNATURE):
        info = _rar4_properties(data=data)
        version = 'RAR 1.5 to 4'
        if info.get('version'):
            version += ' (unpack version {}.{})'.format(
                info['version'] // 10, info['version'] % 10
            )
    else:
        return []
    fields = [('RAR version', version)]
    if info['flags']:
        fields.append(('Properties', ', '.join(info['flags'])))
    if info.get('method'):
        method = info['method']
        if info.get('dictionary'):
            method += ', dictionary {}'.format(_format_size(info['dictionary']))
        fields.append(('Method', method))
    if info.get('system'):
        fields.append(('Created on', info['system']))
    if info.get('headers_encrypted'):
        fields.append(('Headers', 'encrypted'))
    if info.get('comment'):
        fields.append(('Comment', info['comment']))
    return fields


# Entries of a RAR archive, read from its headers: for the archives that
# libarchive stops reading (RAR 1.5 to 4 solid archives, RAR 1.5).

RAR_BLOCK_READ_SIZE = 64 * 1024
RAR_ENTRIES_MAXIMUM = 20000


class _BlockReader:
    """Reads of the file at an offset, the file being read where needed."""
    def __init__(self, file_object):
        self.file_object = file_object
        file_object.seek(0, 2)
        self.size = file_object.tell()

    def read(self, offset, size):
        if offset >= self.size:
            return b''
        self.file_object.seek(offset)
        return self.file_object.read(size)


def _dos_time(value):
    date, clock = value >> 16, value & 0xffff
    try:
        return datetime(
            ((date >> 9) & 0x7f) + 1980, (date >> 5) & 0x0f, date & 0x1f,
            clock >> 11, (clock >> 5) & 0x3f, (clock & 0x1f) * 2
        )
    except ValueError:
        return None


def _rar4_name(raw, flags):
    if flags & 0x0200:
        # Unicode name: the ASCII form, then a NUL and the Unicode form.
        raw = raw.split(b'\x00', 1)[0]
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw.decode('cp437')


def _list_rar4(reader, entries):
    position = len(RAR4_SIGNATURE)
    continues = False
    while len(entries) < RAR_ENTRIES_MAXIMUM:
        head = reader.read(position, RAR_BLOCK_READ_SIZE)
        if len(head) < 7:
            break
        _, kind, flags, size = struct.unpack_from('<HBHH', head, 0)
        if size < 7:
            break
        add_size = 0
        if flags & 0x8000 and len(head) >= 11:
            add_size = struct.unpack_from('<I', head, 7)[0]
        if kind == 0x73 and flags & 0x0080:
            # Encrypted headers.
            return None
        if kind == 0x74 and len(head) >= 32:
            unpacked = struct.unpack_from('<I', head, 11)[0]
            name_size = struct.unpack_from('<H', head, 26)[0]
            name_start = 32
            if flags & 0x0100 and len(head) >= 40:
                add_size += struct.unpack_from('<I', head, 32)[0] << 32
                unpacked += struct.unpack_from('<I', head, 36)[0] << 32
                name_start = 40
            attributes = struct.unpack_from('<I', head, 28)[0]
            if flags & 0x00e0 == 0x00e0:
                kind_name = 'directory'
            elif head[15] == 3 and attributes & 0o170000 == 0o120000:
                # Unix symbolic link: its target is the data.
                kind_name = 'link'
            else:
                kind_name = 'file'
            entries.append(
                {
                    'path': _rar4_name(
                        raw=head[name_start:name_start + name_size], flags=flags
                    ).replace('\\', '/'),
                    'size': unpacked if kind_name == 'file' else None,
                    'modified': _dos_time(struct.unpack_from('<I', head, 20)[0]),
                    'kind': kind_name, 'encrypted': bool(flags & 0x0004)
                }
            )
            continues = bool(flags & 0x0002)
        elif kind == 0x7b:
            break
        position += size + add_size
    return continues


def _list_rar5(reader, entries):
    position = len(RAR5_SIGNATURE)
    continues = False
    while len(entries) < RAR_ENTRIES_MAXIMUM:
        head = reader.read(position, RAR_BLOCK_READ_SIZE)
        if len(head) < 5:
            break
        size, start = _vint(head, 4)
        end = start + size
        if end > len(head):
            # A header larger than the block read: read all of it.
            if size > HEAD_SIZE_MAXIMUM:
                break
            head = reader.read(position, end)
            if len(head) < end:
                break
        if zlib.crc32(head[4:end]) != struct.unpack_from('<I', head, 0)[0]:
            break
        kind, cursor = _vint(head, start)
        flags, cursor = _vint(head, cursor)
        extra_size = data_size = 0
        if flags & 0x0001:
            extra_size, cursor = _vint(head, cursor)
        if flags & 0x0002:
            data_size, cursor = _vint(head, cursor)
        if kind == 4:
            return None
        if kind == 2:
            file_flags, cursor = _vint(head, cursor)
            unpacked, cursor = _vint(head, cursor)
            _, cursor = _vint(head, cursor)  # Attributes.
            modified = None
            if file_flags & 0x0002:
                # Unix time, shown in the time zone of the installation.
                modified = struct.unpack_from('<I', head, cursor)[0]
                cursor += 4
            if file_flags & 0x0004:
                cursor += 4
            _, cursor = _vint(head, cursor)  # Compression.
            _, cursor = _vint(head, cursor)  # System.
            name_length, cursor = _vint(head, cursor)
            name = head[cursor:cursor + name_length].decode('utf-8', 'replace')
            records = _rar5_extra_records(
                data=head, start=end - extra_size, end=end
            )
            if 0x04 in records:
                # File version, named as libarchive does: name;version.
                _, version_position = _vint(head, records[0x04])
                version, _ = _vint(head, version_position)
                name = '{};{}'.format(name, version)
            if file_flags & 0x0001:
                kind_name = 'directory'
            elif 0x05 in records:
                # Redirection record: symbolic link, junction or hard link.
                kind_name = 'link'
            else:
                kind_name = 'file'
            # A file split between volumes is listed in its first one.
            if not flags & 0x0008:
                entries.append(
                    {
                        'path': name,
                        'size': unpacked if kind_name == 'file' and not file_flags & 0x0008 else None,
                        'modified': modified, 'kind': kind_name,
                        'encrypted': 0x01 in records
                    }
                )
            continues = bool(flags & 0x0010)
        elif kind == 5:
            break
        # end is counted from the start of the header, like data_size.
        if end + data_size <= 0:
            break
        position += end + data_size
    return continues


def list_rar_entries(file_object):
    """
    Entries of a RAR archive read from its headers, and whether the last
    one continues in the next volume; None when the headers are encrypted
    or the file is not a RAR archive.
    """
    reader = _BlockReader(file_object=file_object)
    try:
        signature = reader.read(0, len(RAR5_SIGNATURE))
        entries = []
        if signature == RAR5_SIGNATURE:
            continues = _list_rar5(reader=reader, entries=entries)
        elif signature.startswith(RAR4_SIGNATURE):
            continues = _list_rar4(reader=reader, entries=entries)
        else:
            return None
    finally:
        file_object.seek(0)
    if continues is None:
        return None
    return entries, continues
