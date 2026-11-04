"""
Reader of the Microsoft Outlook .msg files, for what this project needs from
them: the sender, the recipients, the subject, the text and the attachments.

Written from the public specification of the format, [MS-OXMSG] "Outlook Item
(.msg) File Format". The package extract-msg did this before, but it is under
the GPLv3, which cannot be combined with this project (GPL-2.0-only), and it
brought pcodedmp, under the same license. A .msg file is an OLE compound file,
which olefile (BSD) reads.

The data comes from outside: a stream cannot be larger than the file, even when
its declared size and its chain of sectors say so, and the number of recipients
and attachments and the depth of the attached messages are limited.
"""
from email.header import decode_header, make_header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.parser import HeaderParser
from functools import cached_property
import logging
import re

import olefile

logger = logging.getLogger(name=__name__)

# The limits of the specification.
ATTACHMENTS_MAXIMUM = 2048
RECIPIENTS_MAXIMUM = 2048
# Attached messages inside attached messages.
EMBEDDED_DEPTH_MAXIMUM = 8

ENCODING_DEFAULT = 'cp1252'
# The code pages that Python does not know under the name cpNNN.
ENCODINGS = {
    20127: 'ascii', 28591: 'iso8859-1', 28592: 'iso8859-2', 28593: 'iso8859-3',
    28594: 'iso8859-4', 28595: 'iso8859-5', 28596: 'iso8859-6',
    28597: 'iso8859-7', 28598: 'iso8859-8', 28599: 'iso8859-9',
    28603: 'iso8859-13', 28605: 'iso8859-15', 50220: 'iso2022_jp',
    50221: 'iso2022_jp', 50222: 'iso2022_jp', 51932: 'euc_jp',
    51936: 'gb2312', 51949: 'euc_kr', 52936: 'hz', 54936: 'gb18030',
    65001: 'utf-8'
}

# The size of the header of the table of the fixed-size properties.
HEADER_SIZE_ATTACHMENT_OR_RECIPIENT = 8
HEADER_SIZE_EMBEDDED_MESSAGE = 24
HEADER_SIZE_MESSAGE = 32

PREFIX_ATTACHMENT = '__attach_version1.0_#'
PREFIX_RECIPIENT = '__recip_version1.0_#'
PREFIX_VALUE = '__substg1.0_'
STREAM_PROPERTIES = '__properties_version1.0'

TYPE_BINARY = '0102'
TYPE_OBJECT = '000D'
TYPE_STRING = '001E'
TYPE_UNICODE = '001F'

PROPERTY_ATTACHMENT_DATA = 0x3701
PROPERTY_ATTACHMENT_FILENAME = 0x3704
PROPERTY_ATTACHMENT_FILENAME_LONG = 0x3707
PROPERTY_BODY = 0x1000
PROPERTY_CODE_PAGE_INTERNET = 0x3FDE
PROPERTY_CODE_PAGE_MESSAGE = 0x3FFD
PROPERTY_DISPLAY_NAME = 0x3001
PROPERTY_EMAIL_ADDRESS = 0x3003
PROPERTY_HEADERS = 0x007D
PROPERTY_RECIPIENT_TYPE = 0x0C15
PROPERTY_SENDER_ADDRESS = 0x0C1F
PROPERTY_SENDER_NAME = 0x0C1A
PROPERTY_SENDER_SMTP_ADDRESS = 0x5D01
PROPERTY_SMTP_ADDRESS = 0x39FE
PROPERTY_SUBJECT = 0x0037

RECIPIENT_TO = 1
RECIPIENT_CC = 2

REGEX_FILENAME = re.compile(pattern=r'[\x00-\x1f/\\:*?"<>|]')
REGEX_FIRST_LINE_NOT_HEADER = re.compile(pattern=r'\A[^:\r\n]*\r?\n')
REGEX_LINE_BREAKS = re.compile(pattern=r'\s*[\r\n]+\s*')
# Exchange addresses of the form /O=.../CN=... are not the ones to show.
REGEX_SMTP_ADDRESS = re.compile(pattern=r'[^@\s/]+@[^@\s]+')


class OutlookMessageError(ValueError):
    """The file is not a .msg file."""


def _format_address(name, address):
    if address and not REGEX_SMTP_ADDRESS.fullmatch(address):
        address = None
    if name and address:
        return '{} <{}>'.format(name, address)
    return name or address or None


class OutlookItem:
    """
    A message, a recipient or an attachment: a storage of the file, with a
    stream for each property of variable size and a table for the others.
    """
    header_size = HEADER_SIZE_ATTACHMENT_OR_RECIPIENT

    def __init__(self, compound_file, encoding, file_size, path):
        self.compound_file = compound_file
        self.encoding = encoding
        self.file_size = file_size
        self.path = path

    def _read_stream(self, name):
        path = self.path + [name]
        try:
            if self.compound_file.get_type(path) != olefile.STGTY_STREAM:
                return None
            if self.compound_file.get_size(path) > self.file_size:
                logger.warning('Stream larger than its file: %s', '/'.join(path))
                return None
            with self.compound_file.openstream(path) as stream:
                return stream.read()
        except (IndexError, OSError, ValueError) as exception:
            logger.debug('Unreadable stream %s: %s', '/'.join(path), exception)
            return None

    @cached_property
    def _fixed_properties(self):
        data = self._read_stream(name=STREAM_PROPERTIES) or b''
        result = {}
        for offset in range(self.header_size, len(data) - 15, 16):
            result[int.from_bytes(data[offset + 2:offset + 4], 'little')] = (
                int.from_bytes(data[offset + 8:offset + 12], 'little')
            )
        return result

    def get_integer(self, identifier):
        return self._fixed_properties.get(identifier)

    def get_binary(self, identifier):
        return self._read_stream(
            name='{}{:04X}{}'.format(PREFIX_VALUE, identifier, TYPE_BINARY)
        )

    def get_string(self, identifier):
        name = '{}{:04X}'.format(PREFIX_VALUE, identifier)
        data = self._read_stream(name=name + TYPE_UNICODE)
        if data is not None:
            return data.decode('utf-16-le', 'replace').rstrip('\x00')

        data = self._read_stream(name=name + TYPE_STRING)
        if data is None:
            return None
        # The code page of the file is often not the one of its 8-bit strings:
        # plain ASCII or UTF-8 announced, with accents of Windows inside.
        try:
            text = data.decode(self.encoding)
        except (LookupError, UnicodeDecodeError):
            text = data.decode(ENCODING_DEFAULT, 'replace')
        return text.rstrip('\x00')

    def get_children(self, maximum, prefix):
        """The storages of a kind inside this one, in the order of their names."""
        depth = len(self.path)
        names = set()
        for path in self.compound_file.listdir(streams=False, storages=True):
            if len(path) == depth + 1 and path[:depth] == self.path and (
                path[depth].lower().startswith(prefix)
            ):
                names.add(path[depth])
        return [self.path + [name] for name in sorted(names)[:maximum]]


class OutlookRecipient(OutlookItem):
    @property
    def address(self):
        return _format_address(
            name=self.get_string(identifier=PROPERTY_DISPLAY_NAME),
            address=self.get_string(identifier=PROPERTY_SMTP_ADDRESS) or
            self.get_string(identifier=PROPERTY_EMAIL_ADDRESS)
        )

    @property
    def kind(self):
        return self.get_integer(identifier=PROPERTY_RECIPIENT_TYPE)


class OutlookAttachment(OutlookItem):
    def __init__(self, depth, index, **kwargs):
        super().__init__(**kwargs)
        self.depth = depth
        self.index = index

    @cached_property
    def embedded_message(self):
        path = self.path + [
            '{}{:04X}{}'.format(
                PREFIX_VALUE, PROPERTY_ATTACHMENT_DATA, TYPE_OBJECT
            )
        ]
        if (
            self.depth < EMBEDDED_DEPTH_MAXIMUM and
            self.compound_file.exists(path + [STREAM_PROPERTIES])
        ):
            return OutlookEmbeddedMessage(
                compound_file=self.compound_file, depth=self.depth + 1,
                file_size=self.file_size, path=path
            )

    @cached_property
    def filename(self):
        filename = (
            self.get_string(identifier=PROPERTY_ATTACHMENT_FILENAME_LONG) or
            self.get_string(identifier=PROPERTY_ATTACHMENT_FILENAME) or
            self.get_string(identifier=PROPERTY_DISPLAY_NAME)
        )
        if self.embedded_message:
            filename = '{}.eml'.format(
                self.embedded_message.subject or filename or 'message'
            )
        filename = REGEX_FILENAME.sub('_', filename or '').strip()
        return filename or 'attachment-{}'.format(self.index + 1)

    @property
    def data(self):
        """The bytes of the attachment; an attached message as an .eml file."""
        if self.embedded_message:
            return self.embedded_message.as_bytes()
        return self.get_binary(identifier=PROPERTY_ATTACHMENT_DATA) or b''


class OutlookMessageBase(OutlookItem):
    def __init__(self, compound_file, depth, file_size, path):
        super().__init__(
            compound_file=compound_file, encoding=ENCODING_DEFAULT,
            file_size=file_size, path=path
        )
        self.depth = depth
        code_page = (
            self.get_integer(identifier=PROPERTY_CODE_PAGE_MESSAGE) or
            self.get_integer(identifier=PROPERTY_CODE_PAGE_INTERNET)
        )
        if code_page:
            self.encoding = ENCODINGS.get(code_page, 'cp{}'.format(code_page))

    @cached_property
    def _headers(self):
        """The Internet headers, in the messages that came from the Internet."""
        text = self.get_string(identifier=PROPERTY_HEADERS)
        if not text:
            return None
        # Exchange starts them with a line of its own.
        return HeaderParser().parsestr(
            REGEX_FIRST_LINE_NOT_HEADER.sub('', text)
        )

    def _get_header(self, name):
        value = self._headers and self._headers.get(name)
        if not value:
            return None
        value = str(value)
        try:
            value = str(make_header(decode_header(value)))
        except (LookupError, UnicodeError, ValueError):
            """Encoded words that cannot be read: left as they are."""
        return REGEX_LINE_BREAKS.sub(' ', value).strip() or None

    def _get_recipients(self, kind):
        return '; '.join(
            item.address for item in self.recipients
            if item.kind == kind and item.address
        ) or None

    @cached_property
    def recipients(self):
        return [
            OutlookRecipient(
                compound_file=self.compound_file, encoding=self.encoding,
                file_size=self.file_size, path=path
            ) for path in self.get_children(
                maximum=RECIPIENTS_MAXIMUM, prefix=PREFIX_RECIPIENT
            )
        ]

    @cached_property
    def attachments(self):
        return [
            OutlookAttachment(
                compound_file=self.compound_file, depth=self.depth,
                encoding=self.encoding, file_size=self.file_size,
                index=index, path=path
            ) for index, path in enumerate(
                self.get_children(
                    maximum=ATTACHMENTS_MAXIMUM, prefix=PREFIX_ATTACHMENT
                )
            )
        ]

    @cached_property
    def body(self):
        return self.get_string(identifier=PROPERTY_BODY) or ''

    @cached_property
    def cc(self):
        return self._get_header(name='Cc') or self._get_recipients(
            kind=RECIPIENT_CC
        )

    @cached_property
    def sender(self):
        return self._get_header(name='From') or _format_address(
            name=self.get_string(identifier=PROPERTY_SENDER_NAME),
            address=self.get_string(identifier=PROPERTY_SENDER_SMTP_ADDRESS) or
            self.get_string(identifier=PROPERTY_SENDER_ADDRESS)
        )

    @cached_property
    def subject(self):
        return self.get_string(identifier=PROPERTY_SUBJECT)

    @cached_property
    def to(self):
        return self._get_header(name='To') or self._get_recipients(
            kind=RECIPIENT_TO
        )

    def as_bytes(self):
        """The message in the format of the .eml files."""
        result = MIMEMultipart()
        for name, value in (
            ('Subject', self.subject), ('From', self.sender), ('To', self.to),
            ('Cc', self.cc)
        ):
            if value:
                result[name] = REGEX_LINE_BREAKS.sub(' ', value)
        result.attach(MIMEText(self.body, 'plain', 'utf-8'))

        # A chain of sectors can give the same content to any number of
        # attachments: together, they are not larger than the file either.
        budget = self.file_size
        for attachment in self.attachments:
            data = attachment.data
            budget -= len(data)
            if budget < 0:
                logger.warning('Attachments larger than their file.')
                break
            part = MIMEApplication(data)
            part.add_header(
                'Content-Disposition', 'attachment',
                filename=('utf-8', '', attachment.filename)
            )
            result.attach(part)

        return result.as_bytes()


class OutlookEmbeddedMessage(OutlookMessageBase):
    header_size = HEADER_SIZE_EMBEDDED_MESSAGE


class OutlookMessage(OutlookMessageBase):
    header_size = HEADER_SIZE_MESSAGE

    def __init__(self, file_object):
        file_object.seek(0, 2)
        file_size = file_object.tell()
        file_object.seek(0)

        try:
            compound_file = olefile.OleFileIO(file_object)
        except (IndexError, OSError, ValueError) as exception:
            raise OutlookMessageError(
                'Not an Outlook message: {}'.format(exception)
            ) from exception

        if not compound_file.exists([STREAM_PROPERTIES]):
            compound_file.close()
            raise OutlookMessageError(
                'Compound file without the properties of a message.'
            )

        super().__init__(
            compound_file=compound_file, depth=0, file_size=file_size, path=[]
        )

    def close(self):
        self.compound_file.close()
