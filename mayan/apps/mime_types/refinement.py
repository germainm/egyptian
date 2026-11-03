"""
Content checks that refine the generic MIME types returned by file(1) for
formats that it does not identify, so that these files reach the converter
path, the parser and the metadata drivers made for them:

- application/zip: office documents whose archive does not start with the
  member that file(1) looks for (DOCX without [Content_Types].xml first,
  OpenDocument files, EPUB books);
- image/tiff: DICOM files preceded by a TIFF header, and raw photos built on
  TIFF (DNG, NEF, ARW, PEF), whose first image is a small preview or the raw
  sensor data, not a picture Pillow can show;
- application/octet-stream: EMF drawings, Panasonic raw photos, DICOM files;
- text/plain: emails whose first header is not one file(1) knows.

Each check reads a few bytes or the archive directory only, and returns the
MIME type unchanged when the content does not match or cannot be read.
"""
import logging
import re
import struct
import zipfile

logger = logging.getLogger(name=__name__)

MIME_TYPE_DICOM = 'application/dicom'
MIME_TYPE_DNG = 'image/x-adobe-dng'
MIME_TYPE_EMAIL = 'message/rfc822'
MIME_TYPE_EMF = 'image/emf'
MIME_TYPE_EPUB = 'application/epub+zip'
MIME_TYPE_PANASONIC_RAW = 'image/x-panasonic-rw2'

DICOM_PREFIX_OFFSET = 128
DICOM_PREFIX = b'DICM'

EMF_HEADER_RECORD_TYPE = b'\x01\x00\x00\x00'
EMF_SIGNATURE_OFFSET = 40
EMF_SIGNATURE = b' EMF'

PANASONIC_RAW_HEADER = b'IIU\x00'

# Main part of each Office Open XML format, the first found wins.
OOXML_MAIN_PARTS = (
    (
        'word/document.xml',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ),
    (
        'xl/workbook.xml',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ),
    (
        'xl/workbook.bin',
        'application/vnd.ms-excel.sheet.binary.macroEnabled.12'
    ),
    (
        'ppt/presentation.xml',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    ),
)
OOXML_CONTENT_TYPES_PART = '[Content_Types].xml'
# The "mimetype" member of OpenDocument files and EPUB books names their
# format; only these values are trusted.
ZIP_MIMETYPE_MEMBER = 'mimetype'
ZIP_MIMETYPE_MEMBER_MAXIMUM_SIZE = 128
ZIP_MIMETYPE_MEMBER_PREFIXES = (
    'application/vnd.oasis.opendocument.', MIME_TYPE_EPUB
)
EPUB_CONTAINER_MEMBER = 'META-INF/container.xml'
REGULAR_EXPRESSION_MIME_TYPE = re.compile(
    pattern=r'^[a-z0-9][a-z0-9.+-]*/[a-z0-9][a-z0-9.+-]*$'
)

TIFF_TAG_NEW_SUBFILE_TYPE = 254
TIFF_TAG_PHOTOMETRIC_INTERPRETATION = 262
TIFF_TAG_MAKE = 271
TIFF_TAG_DNG_VERSION = 50706
TIFF_TYPE_ASCII = 2
TIFF_TYPE_SHORT = 3
TIFF_TYPE_LONG = 4
TIFF_MAXIMUM_IFD_ENTRIES = 1024
TIFF_MAXIMUM_MAKE_LENGTH = 64
# Raw sensor data: color filter array and linear raw.
TIFF_PHOTOMETRIC_RAW = (32803, 34892)
TIFF_NEW_SUBFILE_TYPE_REDUCED_RESOLUTION = 1
# Camera makers whose raw photos are TIFF files, by the start of the Make
# tag, upper case.
TIFF_RAW_MAKES = (
    ('NIKON', 'image/x-nikon-nef'),
    ('SONY', 'image/x-sony-arw'),
    ('PENTAX', 'image/x-pentax-pef'),
    # Pentax cameras are made by Ricoh Imaging since 2011.
    ('RICOH', 'image/x-pentax-pef'),
    ('CANON', 'image/x-canon-cr2'),
    ('OLYMPUS', 'image/x-olympus-orf'),
    ('OM DIGITAL', 'image/x-olympus-orf'),
)

EMAIL_HEADER_READ_SIZE = 16384
EMAIL_HEADER_MINIMUM_COUNT = 3
EMAIL_HEADER_MINIMUM_KNOWN = 2
EMAIL_HEADERS_KNOWN = frozenset(
    (
        'cc', 'date', 'delivered-to', 'from', 'message-id', 'mime-version',
        'received', 'reply-to', 'return-path', 'subject', 'to'
    )
)
# Headers that only an email has, one of them is required.
EMAIL_HEADERS_REQUIRED = frozenset(
    ('from', 'message-id', 'mime-version', 'received', 'return-path')
)
REGULAR_EXPRESSION_EMAIL_HEADER = re.compile(
    pattern=r'^([!-9;-~]+):'
)


def _read_at(file_object, offset, size):
    file_object.seek(offset)
    return file_object.read(size)


def get_zip_mime_type(file_object):
    try:
        with zipfile.ZipFile(file=file_object) as zip_file:
            names = set(zip_file.namelist())

            if OOXML_CONTENT_TYPES_PART in names:
                for part_name, mime_type in OOXML_MAIN_PARTS:
                    if part_name in names:
                        return mime_type

            if ZIP_MIMETYPE_MEMBER in names:
                member_info = zip_file.getinfo(name=ZIP_MIMETYPE_MEMBER)
                if member_info.file_size <= ZIP_MIMETYPE_MEMBER_MAXIMUM_SIZE:
                    value = zip_file.read(name=ZIP_MIMETYPE_MEMBER).decode(
                        encoding='ascii', errors='replace'
                    ).strip()
                    if REGULAR_EXPRESSION_MIME_TYPE.match(value) and value.startswith(ZIP_MIMETYPE_MEMBER_PREFIXES):
                        return value

            if EPUB_CONTAINER_MEMBER in names:
                return MIME_TYPE_EPUB
    except (zipfile.BadZipFile, KeyError, OSError, RuntimeError, ValueError) as exception:
        logger.debug('Unable to read the ZIP archive; %s', exception)


def is_dicom(file_object):
    return _read_at(
        file_object=file_object, offset=DICOM_PREFIX_OFFSET,
        size=len(DICOM_PREFIX)
    ) == DICOM_PREFIX


def get_tiff_first_ifd_tags(file_object):
    """
    Tags NewSubfileType, PhotometricInterpretation, Make and DNGVersion of
    the first image file directory, as a dictionary; None when the file is
    not a readable TIFF file.
    """
    header = _read_at(file_object=file_object, offset=0, size=8)
    if header[:4] == b'II*\x00':
        byte_order = '<'
    elif header[:4] == b'MM\x00*':
        byte_order = '>'
    else:
        return None

    (ifd_offset,) = struct.unpack(byte_order + 'I', header[4:8])
    entry_count_data = _read_at(
        file_object=file_object, offset=ifd_offset, size=2
    )
    if len(entry_count_data) != 2:
        return None

    (entry_count,) = struct.unpack(byte_order + 'H', entry_count_data)
    if entry_count > TIFF_MAXIMUM_IFD_ENTRIES:
        return None

    entries = file_object.read(12 * entry_count)
    if len(entries) != 12 * entry_count:
        return None

    tags = {}
    for index in range(entry_count):
        tag, field_type, count, value = struct.unpack(
            byte_order + 'HHI4s', entries[12 * index: 12 * index + 12]
        )
        if tag == TIFF_TAG_DNG_VERSION:
            tags[tag] = True
        elif tag in (TIFF_TAG_NEW_SUBFILE_TYPE, TIFF_TAG_PHOTOMETRIC_INTERPRETATION):
            if field_type == TIFF_TYPE_SHORT:
                (tags[tag],) = struct.unpack(byte_order + 'H', value[:2])
            elif field_type == TIFF_TYPE_LONG:
                (tags[tag],) = struct.unpack(byte_order + 'I', value)
        elif tag == TIFF_TAG_MAKE and field_type == TIFF_TYPE_ASCII:
            count = min(count, TIFF_MAXIMUM_MAKE_LENGTH)
            if count <= 4:
                make = value[:count]
            else:
                (make_offset,) = struct.unpack(byte_order + 'I', value)
                position = file_object.tell()
                make = _read_at(
                    file_object=file_object, offset=make_offset, size=count
                )
                file_object.seek(position)
            tags[tag] = make.split(b'\x00')[0].decode(
                encoding='latin-1'
            ).strip().upper()

    return tags


def get_tiff_raw_mime_type(file_object):
    tags = get_tiff_first_ifd_tags(file_object=file_object)
    if not tags:
        return None

    if tags.get(TIFF_TAG_DNG_VERSION):
        return MIME_TYPE_DNG

    is_raw_layout = (
        tags.get(TIFF_TAG_NEW_SUBFILE_TYPE) == TIFF_NEW_SUBFILE_TYPE_REDUCED_RESOLUTION or
        tags.get(TIFF_TAG_PHOTOMETRIC_INTERPRETATION) in TIFF_PHOTOMETRIC_RAW
    )
    if not is_raw_layout:
        return None

    make = tags.get(TIFF_TAG_MAKE, '')
    for make_prefix, mime_type in TIFF_RAW_MAKES:
        if make.startswith(make_prefix):
            return mime_type


def is_emf(file_object):
    header = _read_at(
        file_object=file_object, offset=0,
        size=EMF_SIGNATURE_OFFSET + len(EMF_SIGNATURE)
    )
    return (
        header[:4] == EMF_HEADER_RECORD_TYPE and
        header[EMF_SIGNATURE_OFFSET:] == EMF_SIGNATURE
    )


def is_email(file_object):
    """
    True when the file starts with a block of email headers: at least three,
    two of them common email headers, one of them a header that only an
    email has (From, Received, Message-ID…), followed by an empty line.
    """
    text = _read_at(
        file_object=file_object, offset=0, size=EMAIL_HEADER_READ_SIZE
    ).decode(encoding='latin-1')
    lines = text.splitlines()
    if lines and lines[0].startswith('From '):
        # Envelope line of an mbox export.
        lines = lines[1:]

    names = []
    for line in lines:
        if not line.strip():
            break
        if line[0] in ' \t':
            # Folded header.
            if not names:
                return False
            continue

        match = REGULAR_EXPRESSION_EMAIL_HEADER.match(line)
        if not match:
            return False
        names.append(match.group(1).lower())
    else:
        # No empty line within the bytes read: not a header block.
        return False

    known = EMAIL_HEADERS_KNOWN.intersection(names)
    return (
        len(names) >= EMAIL_HEADER_MINIMUM_COUNT and
        len(known) >= EMAIL_HEADER_MINIMUM_KNOWN and
        bool(EMAIL_HEADERS_REQUIRED.intersection(names))
    )


def refine_mime_type(file_object, mime_type):
    """
    Return the MIME type of the file, refined from its content when file(1)
    gave a generic one; the file position is restored.
    """
    try:
        position = file_object.tell()
    except (AttributeError, OSError):
        position = 0

    try:
        if mime_type == 'application/zip':
            return get_zip_mime_type(file_object=file_object) or mime_type

        if mime_type == 'image/tiff':
            if is_dicom(file_object=file_object):
                return MIME_TYPE_DICOM
            return get_tiff_raw_mime_type(file_object=file_object) or mime_type

        if mime_type == 'application/octet-stream':
            if is_dicom(file_object=file_object):
                return MIME_TYPE_DICOM
            if is_emf(file_object=file_object):
                return MIME_TYPE_EMF
            header = _read_at(
                file_object=file_object, offset=0,
                size=len(PANASONIC_RAW_HEADER)
            )
            if header == PANASONIC_RAW_HEADER:
                return MIME_TYPE_PANASONIC_RAW
            return mime_type

        if mime_type == 'text/plain':
            if is_email(file_object=file_object):
                return MIME_TYPE_EMAIL
            return mime_type
    except (OSError, ValueError, struct.error) as exception:
        logger.debug(
            'Unable to refine the MIME type "%s"; %s', mime_type, exception
        )
    finally:
        try:
            file_object.seek(position)
        except (AttributeError, OSError):
            pass

    return mime_type
