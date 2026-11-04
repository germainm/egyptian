"""
Reader of the Outlook .msg files. The files are made here, from the public
specification of their format: their results were compared once with those of
Apache POI test files and of the package that this reader replaces.
"""
import email
import email.policy
import io
import struct

from django.test import SimpleTestCase

from ..compressed_files import MsgArchive
from ..outlook import OutlookMessage, OutlookMessageError

END_OF_CHAIN = 0xFFFFFFFE
FAT_SECTOR = 0xFFFFFFFD
FREE = 0xFFFFFFFF
NO_STREAM = 0xFFFFFFFF
MINI_CUTOFF = 4096
MINI_SIZE = 64
SECTOR_SIZE = 512


def make_compound_file(tree):
    """
    An OLE compound file (version 3) from a tree of dictionaries (storages) and
    bytes (streams): nothing writes them in Python under a license that this
    project could use.
    """
    entries = []

    def add(name, content, kind):
        index = len(entries)
        entry = {
            'child': NO_STREAM, 'content': content, 'kind': kind, 'name': name,
            'right': NO_STREAM, 'size': 0, 'start': END_OF_CHAIN
        }
        entries.append(entry)
        if isinstance(content, dict):
            previous = None
            for child_name in sorted(
                content, key=lambda item: (len(item), item.upper())
            ):
                child = content[child_name]
                child_index = add(
                    child_name, child, 1 if isinstance(child, dict) else 2
                )
                if previous is None:
                    entry['child'] = child_index
                else:
                    entries[previous]['right'] = child_index
                previous = child_index
        return index

    add('Root Entry', tree, 5)

    mini_stream = bytearray()
    mini_fat = []
    big_streams = []
    for entry in entries:
        content = entry['content']
        if isinstance(content, dict) or not content:
            continue
        entry['size'] = len(content)
        if len(content) < MINI_CUTOFF:
            entry['start'] = len(mini_fat)
            count = (len(content) + MINI_SIZE - 1) // MINI_SIZE
            mini_fat.extend(range(len(mini_fat) + 1, len(mini_fat) + count))
            mini_fat.append(END_OF_CHAIN)
            mini_stream += content.ljust(count * MINI_SIZE, b'\x00')
        else:
            big_streams.append(entry)

    def sectors(size):
        return (size + SECTOR_SIZE - 1) // SECTOR_SIZE

    directory_sectors = sectors(len(entries) * 128)
    mini_fat_sectors = sectors(len(mini_fat) * 4)
    mini_stream_sectors = sectors(len(mini_stream))
    used = directory_sectors + mini_fat_sectors + mini_stream_sectors + sum(
        sectors(entry['size']) for entry in big_streams
    )
    fat_sectors = 1
    while fat_sectors + used > fat_sectors * (SECTOR_SIZE // 4):
        fat_sectors += 1

    fat = [FAT_SECTOR] * fat_sectors

    def chain(count):
        if not count:
            return END_OF_CHAIN
        start = len(fat)
        fat.extend(range(start + 1, start + count))
        fat.append(END_OF_CHAIN)
        return start

    directory_start = chain(directory_sectors)
    mini_fat_start = chain(mini_fat_sectors)
    entries[0]['start'] = chain(mini_stream_sectors)
    entries[0]['size'] = len(mini_stream)
    for entry in big_streams:
        entry['start'] = chain(sectors(entry['size']))
    fat.extend([FREE] * (fat_sectors * (SECTOR_SIZE // 4) - len(fat)))

    directory = bytearray()
    for entry in entries:
        name = entry['name'].encode('utf-16-le')
        directory += (
            name.ljust(64, b'\x00') + struct.pack(
                '<HBBIII', len(name) + 2, entry['kind'], 1, NO_STREAM,
                entry['right'], entry['child']
            ) + bytes(16 + 4 + 16) + struct.pack(
                '<IQ', entry['start'], entry['size']
            )
        )

    header = (
        bytes.fromhex('D0CF11E0A1B11AE1') + bytes(16) +
        struct.pack('<HHHHH', 0x3E, 3, 0xFFFE, 9, 6) + bytes(6) + struct.pack(
            '<IIIIIIIII', 0, fat_sectors, directory_start, 0, MINI_CUTOFF,
            mini_fat_start, mini_fat_sectors, END_OF_CHAIN, 0
        ) + struct.pack(
            '<109I', *(
                list(range(fat_sectors)) + [FREE] * (109 - fat_sectors)
            )
        )
    )

    def pad(data):
        return bytes(data).ljust(sectors(len(data)) * SECTOR_SIZE, b'\x00')

    return b''.join(
        [
            header, struct.pack('<{}I'.format(len(fat)), *fat),
            pad(directory),
            pad(struct.pack('<{}I'.format(len(mini_fat)), *mini_fat)),
            pad(mini_stream)
        ] + [pad(entry['content']) for entry in big_streams]
    )


def properties(values, header_size=32):
    """The table of the fixed-size properties, {identifier: integer}."""
    return bytes(header_size) + b''.join(
        struct.pack('<HHIIxxxx', 3, identifier, 6, value)
        for identifier, value in values.items()
    )


def unicode_stream(identifier):
    return '__substg1.0_{:04X}001F'.format(identifier)


def string_stream(identifier):
    return '__substg1.0_{:04X}001E'.format(identifier)


def text(value):
    return value.encode('utf-16-le')


def recipient(name, address, kind):
    return {
        '__properties_version1.0': properties({0x0C15: kind}, header_size=8),
        unicode_stream(0x3001): text(name),
        unicode_stream(0x39FE): text(address)
    }


def make_message(**kwargs):
    tree = {
        '__properties_version1.0': properties({0x3FFD: 1252}),
        '__nameid_version1.0': {},
        unicode_stream(0x0037): text('Facture été'),
        unicode_stream(0x0C1A): text('Alice'),
        unicode_stream(0x5D01): text('alice@example.com'),
        unicode_stream(0x1000): text('Le corps\r\ndu message.\x00'),
        '__recip_version1.0_#00000000': recipient('Bob', 'bob@example.com', 1),
        '__recip_version1.0_#00000001': recipient('Carol', 'carol@example.com', 1),
        '__recip_version1.0_#00000002': recipient('Dan', 'dan@example.com', 2),
        '__recip_version1.0_#00000003': recipient('Eve', 'eve@example.com', 3),
        '__attach_version1.0_#00000000': {
            '__properties_version1.0': properties({0x3705: 1}, header_size=8),
            unicode_stream(0x3707): text('facture.pdf'),
            '__substg1.0_37010102': b'%PDF-' + b'x' * 9000
        },
        '__attach_version1.0_#00000001': {
            '__properties_version1.0': properties({0x3705: 1}, header_size=8),
            unicode_stream(0x3704): text('COURT.TXT'),
            '__substg1.0_37010102': b'petit'
        }
    }
    tree.update(kwargs)
    return io.BytesIO(make_compound_file(tree))


class OutlookMessageTestCase(SimpleTestCase):
    def test_properties(self):
        message = OutlookMessage(file_object=make_message())
        self.assertEqual(message.subject, 'Facture été')
        self.assertEqual(message.sender, 'Alice <alice@example.com>')
        self.assertEqual(
            message.to, 'Bob <bob@example.com>; Carol <carol@example.com>'
        )
        self.assertEqual(message.cc, 'Dan <dan@example.com>')
        self.assertEqual(message.body, 'Le corps\r\ndu message.')

    def test_attachments_large_and_small_streams(self):
        message = OutlookMessage(file_object=make_message())
        self.assertEqual(
            [
                (item.filename, item.data[:5], len(item.data))
                for item in message.attachments
            ], [('facture.pdf', b'%PDF-', 9005), ('COURT.TXT', b'petit', 5)]
        )

    def test_attachment_without_a_name(self):
        message = OutlookMessage(
            file_object=make_message(
                **{
                    '__attach_version1.0_#00000000': {
                        '__substg1.0_37010102': b'data'
                    }, '__attach_version1.0_#00000001': {}
                }
            )
        )
        self.assertEqual(message.attachments[0].filename, 'attachment-1')
        self.assertEqual(message.attachments[0].data, b'data')
        self.assertEqual(message.attachments[1].data, b'')

    def test_internet_headers_come_first_and_are_decoded(self):
        headers = (
            'Microsoft Mail Internet Headers Version 2.0\r\n'
            'From: =?UTF-8?B?w4l0w6k=?= <ete@example.com>\r\n'
            'To: "Bob, Jr" <bob@example.com>,\r\n <carol@example.com>\r\n'
            'Subject: ignored\r\n\r\n'
        )
        message = OutlookMessage(
            file_object=make_message(**{unicode_stream(0x007D): text(headers)})
        )
        self.assertEqual(message.sender, 'Été <ete@example.com>')
        self.assertEqual(
            message.to, '"Bob, Jr" <bob@example.com>, <carol@example.com>'
        )
        self.assertEqual(message.cc, 'Dan <dan@example.com>')
        self.assertEqual(message.subject, 'Facture été')

    def test_address_that_is_not_an_internet_one(self):
        message = OutlookMessage(
            file_object=io.BytesIO(
                make_compound_file(
                    {
                        '__properties_version1.0': properties({}),
                        unicode_stream(0x0C1A): text('Alice'),
                        unicode_stream(0x0C1F): text(
                            '/O=FIRST/OU=ADMIN/CN=RECIPIENTS/CN=ALICE@HOST'
                        ),
                        '__recip_version1.0_#00000000': {
                            '__properties_version1.0': properties(
                                {0x0C15: 1}, header_size=8
                            ), unicode_stream(0x3001): text('Bob')
                        }
                    }
                )
            )
        )
        self.assertEqual(message.sender, 'Alice')
        self.assertEqual(message.to, 'Bob')
        self.assertIsNone(message.cc)

    def test_8_bit_strings(self):
        cases = (
            # The code page of the message.
            ({0x3FFD: 1251}, 'автоматически'.encode('cp1251'), 'автоматически'),
            # Without it, the one of its Internet form.
            ({0x3FDE: 950}, '格式測試'.encode('big5'), '格式測試'),
            # Announced ASCII or UTF-8, with accents of Windows inside.
            ({0x3FDE: 20127}, 'été'.encode('cp1252'), 'été'),
            ({0x3FDE: 65001}, 'été'.encode('cp1252'), 'été'),
            # Unknown, and none.
            ({0x3FFD: 99999}, 'été'.encode('cp1252'), 'été'),
            ({}, 'été'.encode('cp1252'), 'été'),
            # The end of a C string.
            ({}, b'sujet\x00', 'sujet')
        )
        for code_pages, data, expected in cases:
            with self.subTest(code_pages=code_pages, expected=expected):
                message = OutlookMessage(
                    file_object=io.BytesIO(
                        make_compound_file(
                            {
                                '__properties_version1.0': properties(code_pages),
                                string_stream(0x0037): data
                            }
                        )
                    )
                )
                self.assertEqual(message.subject, expected)

    def test_attached_message_as_an_eml_file(self):
        inner = {
            # The table of an attached message has a header of its own size.
            '__properties_version1.0': properties({0x3FFD: 1251}, header_size=24),
            string_stream(0x0037): 'Message: joint/я'.encode('cp1251'),
            unicode_stream(0x0C1A): text('Fay'),
            unicode_stream(0x1000): text('Corps joint.'),
            '__recip_version1.0_#00000000': recipient('Gil', 'gil@example.com', 1),
            '__attach_version1.0_#00000000': {
                unicode_stream(0x3707): text('annexe.txt'),
                '__substg1.0_37010102': b'annexe'
            }
        }
        message = OutlookMessage(
            file_object=make_message(
                **{
                    '__attach_version1.0_#00000000': {
                        '__properties_version1.0': properties(
                            {0x3705: 5}, header_size=8
                        ), '__substg1.0_3701000D': inner
                    }
                }
            )
        )
        attachment = message.attachments[0]
        self.assertEqual(attachment.filename, 'Message_ joint_я.eml')

        result = email.message_from_bytes(
            attachment.data, policy=email.policy.default
        )
        self.assertEqual(result['Subject'], 'Message: joint/я')
        self.assertEqual(result['To'], 'Gil <gil@example.com>')
        self.assertEqual(result.get_body().get_content().strip(), 'Corps joint.')
        self.assertEqual(
            [
                (item.get_filename(), item.get_content())
                for item in result.iter_attachments()
            ], [('annexe.txt', b'annexe')]
        )

    def test_attached_messages_too_deep(self):
        tree = {'__properties_version1.0': properties({}, header_size=24)}
        for _ in range(12):
            tree = {
                '__properties_version1.0': properties({}, header_size=24),
                unicode_stream(0x0037): text('niveau'),
                '__attach_version1.0_#00000000': {
                    '__substg1.0_3701000D': tree
                }
            }
        tree['__properties_version1.0'] = properties({})
        message = OutlookMessage(file_object=io.BytesIO(make_compound_file(tree)))
        self.assertTrue(message.attachments[0].data)

        depth = 0
        attachment = message.attachments[0]
        while attachment.embedded_message:
            depth += 1
            attachment = attachment.embedded_message.attachments[0]
        self.assertEqual(depth, 8)
        self.assertEqual(attachment.data, b'')

    def test_not_a_message(self):
        for name, data in (
            ('not a compound file', b'bonjour' * 200),
            ('empty', b''),
            ('other compound file', make_compound_file({'WordDocument': b'x' * 100})),
            ('truncated header', make_compound_file({'a': b'x'})[:100])
        ):
            with self.subTest(name=name):
                with self.assertRaises(OutlookMessageError):
                    OutlookMessage(file_object=io.BytesIO(data))

    def test_stream_larger_than_its_file(self):
        data = bytearray(make_message().getvalue())
        # The declared size of the entry of a stream, in the directory.
        name = '__substg1.0_1000001F'.encode('utf-16-le')
        position = data.index(name)
        data[position + 120:position + 124] = struct.pack('<I', 0x40000000)
        with self.assertLogs('mayan.apps.storage.outlook', level='WARNING'):
            message = OutlookMessage(file_object=io.BytesIO(bytes(data)))
            self.assertEqual(message.body, '')

    def test_damaged_files_never_raise_anything_else(self):
        import random

        generator = random.Random(9)
        original = make_message().getvalue()
        for _ in range(150):
            data = bytearray(original)
            for _ in range(generator.randrange(1, 40)):
                data[generator.randrange(len(data))] = generator.randrange(256)
            try:
                message = OutlookMessage(file_object=io.BytesIO(bytes(data)))
            except OutlookMessageError:
                continue
            message.subject, message.sender, message.to, message.cc, message.body
            for attachment in message.attachments:
                attachment.filename, attachment.data


class MsgArchiveTestCase(SimpleTestCase):
    def get_archive(self, **kwargs):
        archive = MsgArchive()
        archive._open(file_object=make_message(**kwargs))
        return archive

    def test_members(self):
        archive = self.get_archive()
        self.assertEqual(
            archive.members(), ['facture.pdf', 'COURT.TXT', 'message.txt']
        )
        self.assertEqual(
            archive.member_contents(filename='COURT.TXT'), b'petit'
        )
        self.assertEqual(
            archive.member_contents(filename='message.txt'),
            'Le corps\r\ndu message.'.encode()
        )
        self.assertEqual(
            archive.open_member(filename='message.txt').read(),
            'Le corps\r\ndu message.'.encode()
        )
        self.assertEqual(
            archive.open_member(filename='COURT.TXT').read(), b'petit'
        )
        archive.close()

    def test_without_body(self):
        archive = MsgArchive()
        archive._open(
            file_object=io.BytesIO(
                make_compound_file({'__properties_version1.0': properties({})})
            )
        )
        self.assertEqual(archive.members(), [])
