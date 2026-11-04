"""
Reader of the Outlook .msg files. The files are made here, from the public
specification of their format: their results were compared once with those of
Apache POI test files and of the package that this reader replaces.
"""
from datetime import datetime, timezone
import email
from email.message import EmailMessage
import email.policy
import email.utils
import io
import struct
from unittest import mock

from django.test import SimpleTestCase

from ..compressed_files import Archive, EMLArchive, MsgArchive
from ..outlook import OutlookMessage, OutlookMessageError

END_OF_CHAIN = 0xFFFFFFFE
FAT_SECTOR = 0xFFFFFFFD
FREE = 0xFFFFFFFF
NO_STREAM = 0xFFFFFFFF
MINI_CUTOFF = 4096
MINI_SIZE = 64
SECTOR_SIZE = 512
# 2026-11-04 12:00:00 UTC, in hundreds of nanoseconds since 1601.
FILE_TIME_2026 = int(
    (
        datetime(2026, 11, 4, 12, tzinfo=timezone.utc) -
        datetime(1601, 1, 1, tzinfo=timezone.utc)
    ).total_seconds()
) * 10000000


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


def properties64(values, header_size=32):
    """The same table, with values of eight bytes: dates."""
    return bytes(header_size) + b''.join(
        struct.pack('<HHIQ', 0x40, identifier, 6, value)
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
            ], [('annexe.txt', 'annexe')]
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

    def test_date(self):
        value = FILE_TIME_2026
        for identifier in (0x0039, 0x0E06):
            with self.subTest(identifier=identifier):
                message = OutlookMessage(
                    file_object=make_message(
                        **{
                            '__properties_version1.0': properties64(
                                {identifier: value, 0x3FFD: 1252}
                            )
                        }
                    )
                )
                self.assertEqual(
                    email.utils.parsedate_to_datetime(message.date).isoformat(),
                    '2026-11-04T12:00:00+00:00'
                )

    def test_date_of_the_internet_headers_comes_first(self):
        message = OutlookMessage(
            file_object=make_message(
                **{
                    unicode_stream(0x007D): text(
                        'Date: Tue, 3 Nov 2026 08:00:00 -0500\r\n\r\n'
                    ), '__properties_version1.0': properties64(
                        {0x0039: FILE_TIME_2026}
                    )
                }
            )
        )
        self.assertEqual(message.date, 'Tue, 3 Nov 2026 08:00:00 -0500')

    def test_date_out_of_range(self):
        message = OutlookMessage(
            file_object=make_message(
                **{'__properties_version1.0': properties64({0x0039: 2 ** 64 - 1})}
            )
        )
        self.assertIsNone(message.date)

    def test_html_body(self):
        cases = (
            # The code page of its Internet form, as binary data.
            (
                '__substg1.0_10130102', {0x3FDE: 1251}, 'я'.encode('cp1251'), 'я'
            ),
            # Announced wrongly.
            ('__substg1.0_10130102', {0x3FDE: 20127}, 'é'.encode(), 'é'),
            ('__substg1.0_10130102', {0x3FDE: 65001}, 'é'.encode('cp1252'), 'é'),
            # Or as a string.
            (unicode_stream(0x1013), {}, text('é'), 'é')
        )
        for name, code_pages, data, expected in cases:
            with self.subTest(name=name, code_pages=code_pages):
                message = OutlookMessage(
                    file_object=make_message(
                        **{
                            '__properties_version1.0': properties(code_pages),
                            name: b'<p>' + data if name.endswith('0102') else text('<p>') + data
                        }
                    )
                )
                self.assertEqual(message.body_html, '<p>' + expected)

    def test_as_bytes(self):
        message = OutlookMessage(
            file_object=make_message(
                **{
                    '__substg1.0_10130102': b'<p><img src="cid:image@x"></p>',
                    '__attach_version1.0_#00000001': {
                        unicode_stream(0x3707): text('image.png'),
                        unicode_stream(0x3712): text('image@x'),
                        '__substg1.0_37010102': b'png'
                    }
                }
            )
        )
        result = email.message_from_bytes(
            message.as_bytes(), policy=email.policy.default
        )
        self.assertEqual(result['Subject'], 'Facture été')
        self.assertEqual(result['From'], 'Alice <alice@example.com>')
        self.assertEqual(
            result['To'], 'Bob <bob@example.com>, Carol <carol@example.com>'
        )
        self.assertEqual(result['Cc'], 'Dan <dan@example.com>')
        self.assertEqual(
            result.get_body(preferencelist=('html',)).get_content().strip(),
            '<p><img src="cid:image@x"></p>'
        )
        self.assertEqual(
            result.get_body(preferencelist=('plain',)).get_content().strip(),
            'Le corps\r\ndu message.'
        )
        parts = list(result.iter_attachments())
        self.assertEqual(
            [
                (item.get_filename(), item.get_content_type())
                for item in parts
            ], [('facture.pdf', 'application/pdf'), ('image.png', 'image/png')]
        )
        self.assertEqual(parts[1]['Content-ID'], '<image@x>')
        self.assertEqual(parts[1].get_content(), b'png')

    def test_names_in_the_headers_of_an_eml_file(self):
        message = OutlookMessage(
            file_object=make_message(
                **{
                    unicode_stream(0x0C1A): text('Cramer, Nick'),
                    unicode_stream(0x0C1F): text('/O=FIRST/CN=NICK'),
                    unicode_stream(0x5D01): text(''),
                    '__recip_version1.0_#00000000': recipient(
                        'Bohn, Shawn (張)', 'shawn@example.com', 1
                    ),
                    '__recip_version1.0_#00000001': {
                        '__properties_version1.0': properties(
                            {0x0C15: 1}, header_size=8
                        ), unicode_stream(0x3001): text('Sans Adresse')
                    }
                }
            )
        )
        result = email.message_from_bytes(
            message.as_bytes(), policy=email.policy.default
        )
        self.assertIn('Cramer, Nick', result['From'])
        self.assertEqual(result['To'].addresses[0].addr_spec, 'shawn@example.com')
        self.assertEqual(result['To'].addresses[0].display_name, 'Bohn, Shawn (張)')
        self.assertIn('Sans Adresse', result['To'])
        # In the driver, as the messages show them.
        self.assertEqual(
            message.to, 'Bohn, Shawn (張) <shawn@example.com>; Sans Adresse'
        )

        message = OutlookMessage(
            file_object=make_message(
                **{
                    unicode_stream(0x0C1A): text('Chang (張), Tests'),
                    unicode_stream(0x5D01): text('')
                }
            )
        )
        result = email.message_from_bytes(
            message.as_bytes(), policy=email.policy.default
        )
        self.assertNotIn('\\', str(result['From']))
        self.assertIn('Chang (張), Tests', str(result['From']))

    def test_declared_type_of_an_attachment(self):
        for declared, filename, expected in (
            ('image/x-truc', 'a.png', 'image/x-truc'),
            ('pas un type', 'a.png', 'image/png'),
            ('message/rfc822', 'a.eml', 'application/octet-stream'),
            ('', 'sans-extension', 'application/octet-stream')
        ):
            with self.subTest(declared=declared, filename=filename):
                message = OutlookMessage(
                    file_object=make_message(
                        **{
                            '__attach_version1.0_#00000000': {
                                unicode_stream(0x370E): text(declared),
                                unicode_stream(0x3707): text(filename),
                                '__substg1.0_37010102': b'x'
                            }
                        }
                    )
                )
                self.assertEqual(message.attachments[0].mime_type, expected)

    def test_attachments_larger_than_the_file_together(self):
        # A chain of sectors gives the same content to all the attachments.
        tree = {
            '__attach_version1.0_#{:08X}'.format(index): {
                unicode_stream(0x3707): text('{}.bin'.format(index)),
                '__substg1.0_37010102': bytes(9000)
            } for index in range(5)
        }
        message = OutlookMessage(file_object=make_message(**tree))
        with mock.patch.object(message, 'file_size', new=20000):
            with self.assertLogs('mayan.apps.storage.outlook', level='WARNING'):
                result = email.message_from_bytes(
                    message.as_bytes(), policy=email.policy.default
                )
        self.assertEqual(len(list(result.iter_attachments())), 2)

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


class ArchiveNamesTestCase(SimpleTestCase):
    def test_unique_names(self):
        taken = set()
        self.assertEqual(
            [
                Archive._get_unique_name(name=name, taken=taken) for name in (
                    'a.pdf', 'a.pdf', 'a.pdf', 'a (2).pdf', 'b', 'b', '.cache'
                )
            ], ['a.pdf', 'a (2).pdf', 'a (3).pdf', 'a (2) (2).pdf', 'b', 'b (2)', '.cache']
        )

    def test_attachments_of_the_same_name_in_an_email(self):
        message = EmailMessage()
        message['Subject'] = 'Sujet'
        message.set_content('Corps')
        message.add_attachment(
            b'premier', maintype='application', subtype='pdf',
            filename='facture.pdf'
        )
        message.add_attachment(
            b'second', maintype='application', subtype='pdf',
            filename='facture.pdf'
        )
        archive = EMLArchive()
        archive._open(file_object=io.BytesIO(message.as_bytes()))

        self.assertEqual(
            archive.members(), ['body', 'facture.pdf', 'facture (2).pdf']
        )
        self.assertEqual(
            archive.member_contents(filename='facture.pdf'), b'premier'
        )
        self.assertEqual(
            archive.open_member(filename='facture (2).pdf').read(), b'second'
        )


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

    def test_attachments_of_the_same_name(self):
        def attachment(data):
            return {
                unicode_stream(0x3707): text('facture.pdf'),
                '__substg1.0_37010102': data
            }

        archive = self.get_archive(
            **{
                '__attach_version1.0_#00000000': attachment(b'premier'),
                '__attach_version1.0_#00000001': attachment(b'second'),
                '__attach_version1.0_#00000002': attachment(b'dernier')
            }
        )
        self.assertEqual(
            archive.members(), [
                'facture.pdf', 'facture (2).pdf', 'facture (3).pdf',
                'message.txt'
            ]
        )
        self.assertEqual(
            [
                member.read() for member in archive.get_members()
            ], [b'premier', b'second', b'dernier', 'Le corps\r\ndu message.'.encode()]
        )
        self.assertEqual(
            archive.open_member(filename='facture (3).pdf').read(), b'dernier'
        )

    def test_attachment_with_the_name_of_the_text(self):
        archive = self.get_archive(
            **{
                '__attach_version1.0_#00000000': {
                    unicode_stream(0x3707): text('message.txt'),
                    '__substg1.0_37010102': b'piece'
                }
            }
        )
        self.assertEqual(
            archive.members(), ['message (2).txt', 'COURT.TXT', 'message.txt']
        )
        self.assertEqual(
            archive.member_contents(filename='message (2).txt'), b'piece'
        )
        self.assertEqual(
            archive.member_contents(filename='message.txt'),
            'Le corps\r\ndu message.'.encode()
        )

    def test_attachment_with_the_name_of_the_text_without_a_text(self):
        archive = MsgArchive()
        archive._open(
            file_object=io.BytesIO(
                make_compound_file(
                    {
                        '__properties_version1.0': properties({}),
                        '__attach_version1.0_#00000000': {
                            unicode_stream(0x3707): text('message.txt'),
                            '__substg1.0_37010102': b'piece'
                        }
                    }
                )
            )
        )
        self.assertEqual(archive.members(), ['message.txt'])
        self.assertEqual(
            archive.member_contents(filename='message.txt'), b'piece'
        )

    def test_unknown_member(self):
        archive = self.get_archive()
        self.assertIsNone(archive.member_contents(filename='absent'))
        self.assertIsNone(archive.open_member(filename='absent'))

    def test_without_body(self):
        archive = MsgArchive()
        archive._open(
            file_object=io.BytesIO(
                make_compound_file({'__properties_version1.0': properties({})})
            )
        )
        self.assertEqual(archive.members(), [])
