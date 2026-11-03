"""
Pages of the archives: listing of ZIP, JAR, TAR and compressed files,
encryption, comments, pseudo entries, budgets, pages and search text.
"""
import gzip
import importlib.util
import io
import struct
import tarfile
import unittest
import zipfile
from unittest import mock

from django.test import SimpleTestCase

from ..renderers import archive
from ..renderers.archive import get_archive_layout, list_archive

LIBARCHIVE = importlib.util.find_spec('libarchive') is not None


def make_zip(entries, comment=b'', encrypted=()):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.comment = comment
        for name, data in entries:
            info = zipfile.ZipInfo(name, date_time=(2024, 5, 1, 12, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zip_file.writestr(info, data)
    data = bytearray(buffer.getvalue())
    # Entries marked encrypted in the central directory: the listing reads
    # the flag only.
    position = data.find(b'PK\x01\x02')
    while position >= 0:
        name_length = struct.unpack_from('<H', data, position + 28)[0]
        name = bytes(data[position + 46:position + 46 + name_length]).decode()
        if name in encrypted:
            flags = struct.unpack_from('<H', data, position + 8)[0]
            struct.pack_into('<H', data, position + 8, flags | 0x1)
        position = data.find(b'PK\x01\x02', position + 4)
    return io.BytesIO(bytes(data))


def make_tar(entries, mode='w:gz'):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode=mode) as tar_file:
        for name, data in entries:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mtime = 1717243200
            info.uname, info.gname = 'alice', 'staff'
            tar_file.addfile(info, io.BytesIO(data))
    buffer.seek(0)
    return buffer


class ZipListingTestCase(SimpleTestCase):
    def test_entries_comment_and_methods(self):
        listing = list_archive(
            file_object=make_zip(
                entries=[('docs/', b''), ('docs/a.txt', b'a' * 1000), ('b.bin', b'b')],
                comment='Archive commentée'.encode()
            ), mime_type='application/zip'
        )
        self.assertEqual(
            [entry['path'] for entry in listing.entries],
            ['docs/', 'docs/a.txt', 'b.bin']
        )
        self.assertEqual(listing.entries[0]['kind'], 'directory')
        self.assertEqual(listing.entries[1]['size'], 1000)
        self.assertEqual(listing.comment, 'Archive commentée')
        self.assertEqual(listing.compression, 'Deflate')
        self.assertTrue(listing.complete)

    def test_encrypted_entries(self):
        listing = list_archive(
            file_object=make_zip(
                entries=[('secret.txt', b'x'), ('public.txt', b'y')],
                encrypted=('secret.txt',)
            ), mime_type='application/zip'
        )
        self.assertEqual(listing.encrypted_entries, 1)
        fields = dict(archive.summary_fields(listing=listing))
        self.assertIn('1 of 2 entries encrypted', fields['Encryption'])

    def test_jar_manifest(self):
        listing = list_archive(
            file_object=make_zip(
                entries=[
                    (
                        'META-INF/MANIFEST.MF',
                        b'Manifest-Version: 1.0\nMain-Class: ca.example.Main\n'
                        b'Implementation-Title: Exemple\n'
                    )
                ]
            ), mime_type='application/java-archive'
        )
        fields = dict(listing.fields)
        self.assertEqual(fields['Manifest: Main-Class'], 'ca.example.Main')
        self.assertEqual(fields['Manifest: Implementation-Title'], 'Exemple')

    def test_damaged_file_gets_a_page(self):
        layout = get_archive_layout(
            file_object=io.BytesIO(b'PK\x03\x04 not a zip file'),
            mime_type='application/zip'
        )
        self.assertEqual(layout.page_count, 1)
        self.assertIn('could not be read', layout.text(page_number=0))
        layout.render(page_number=0)

    def test_entry_limit(self):
        with mock.patch.object(archive, 'ENTRIES_MAXIMUM', 5):
            listing = list_archive(
                file_object=make_zip(
                    entries=[('f{}.txt'.format(index), b'x') for index in range(9)]
                ), mime_type='application/zip'
            )
        self.assertEqual(listing.entries_read, 5)
        self.assertFalse(listing.complete)
        self.assertIn('Listing stopped after 5 entries', ' '.join(listing.notes))


class PagesTestCase(SimpleTestCase):
    def test_pages_and_search_text(self):
        entries = [('dossier/fiche_{:04d}.txt'.format(index), b'x') for index in range(150)]
        with mock.patch.object(archive, 'ENTRIES_SHOWN_MAXIMUM', 120):
            layout = get_archive_layout(
                file_object=make_zip(entries=entries), mime_type='application/zip'
            )
            self.assertGreater(layout.page_count, 1)
            texts = [layout.text(page_number=page) for page in range(layout.page_count)]
            image = layout.render(page_number=layout.page_count - 1)
        self.assertEqual(image.size, (archive.PAGE_WIDTH, archive.PAGE_HEIGHT))
        self.assertIn('ZIP archive', texts[0])
        # Every entry is in the text of a page, the ones not shown on the
        # pages in the text of the last one.
        for name, _ in entries:
            self.assertTrue(any(name in text for text in texts), name)
        self.assertIn('dossier/fiche_0149.txt', texts[-1])

    def test_out_of_range_page(self):
        layout = get_archive_layout(
            file_object=make_zip(entries=[('a.txt', b'a')]),
            mime_type='application/zip'
        )
        self.assertEqual(layout.page_count, 1)
        layout.render(page_number=5)

    def test_sizes(self):
        self.assertEqual(archive.format_size(0), '0 B')
        self.assertEqual(archive.format_size(1536), '1.5 KB')
        self.assertEqual(archive.format_size(5 * 1024 ** 3), '5.0 GB')


@unittest.skipUnless(LIBARCHIVE, 'libarchive-c not installed')
class LibarchiveListingTestCase(SimpleTestCase):
    def test_tar_gz(self):
        listing = list_archive(
            file_object=make_tar(entries=[('projet/a.txt', b'a' * 10), ('b.txt', b'b')]),
            mime_type='application/gzip'
        )
        self.assertEqual(listing.title, 'TAR archive (gzip)')
        self.assertEqual(listing.compression, 'gzip')
        self.assertEqual([entry['path'] for entry in listing.entries], ['projet/a.txt', 'b.txt'])
        self.assertEqual(listing.entries[0]['owner'], 'alice/staff')
        self.assertIn(('Owners', 'alice/staff (2)'), listing.fields)

    def test_uncompressed_tar(self):
        listing = list_archive(
            file_object=make_tar(entries=[('a.txt', b'a' * 5000)], mode='w'),
            mime_type='application/x-tar'
        )
        self.assertEqual(listing.entries[0]['size'], 5000)
        self.assertEqual(listing.compression, '')

    def test_single_compressed_file(self):
        buffer = io.BytesIO()
        with gzip.GzipFile(filename='notes.txt', mode='wb', fileobj=buffer, mtime=1717243200) as file:
            file.write(b'Premiere ligne\nDeuxieme ligne\n' * 10)
        buffer.seek(0)
        listing = list_archive(file_object=buffer, mime_type='application/gzip')
        self.assertEqual(listing.title, 'Compressed file (gzip)')
        self.assertEqual(listing.uncompressed_size, 300)
        self.assertEqual(dict(listing.fields)['Original name'], 'notes.txt')
        self.assertEqual(listing.preview[:2], ['Premiere ligne', 'Deuxieme ligne'])

    def test_zeros_are_not_an_empty_tar(self):
        listing = list_archive(
            file_object=io.BytesIO(gzip.compress(bytes(100000))),
            mime_type='application/gzip'
        )
        self.assertEqual(listing.title, 'Compressed file (gzip)')
        self.assertEqual(listing.uncompressed_size, 100000)

    def test_decompression_budget(self):
        data = make_tar(entries=[('zeros.bin', bytes(8 * 1024 * 1024)), ('after.txt', b'x')])
        with mock.patch.object(archive, 'DECOMPRESSED_BYTES_MAXIMUM', 1024 * 1024):
            listing = list_archive(file_object=data, mime_type='application/gzip')
        self.assertFalse(listing.complete)
        self.assertIn('decompressed', listing.stop_reason)
        self.assertEqual([entry['path'] for entry in listing.entries], ['zeros.bin'])

    def test_no_other_format_is_tried(self):
        # A text file named in an mtree listing would be read as a list of
        # files of the server: only the formats of the MIME type are enabled.
        data = io.BytesIO(b'#mtree\n/etc/passwd type=file\n')
        listing = list_archive(file_object=data, mime_type='application/x-tar')
        self.assertEqual(listing.entries, [])
        self.assertIn('could not be read', ' '.join(listing.notes))

    def test_pseudo_entries_skipped(self):
        listing = archive.ArchiveListing(title='ISO')
        listing.add(path='.')
        listing.add(path='//')
        listing.add(path='real.txt')
        self.assertEqual([entry['path'] for entry in listing.entries], ['real.txt'])


class WithoutLibarchiveTestCase(SimpleTestCase):
    def test_note_when_libarchive_is_missing(self):
        with mock.patch.dict('sys.modules', {'libarchive': None}):
            listing = list_archive(
                file_object=io.BytesIO(b'7z\xbc\xaf\x27\x1c'),
                mime_type='application/x-7z-compressed'
            )
        self.assertIn('libarchive-c', ' '.join(listing.notes))

    def test_zip_without_libarchive(self):
        with mock.patch.dict('sys.modules', {'libarchive': None}):
            listing = list_archive(
                file_object=make_zip(entries=[('a.txt', b'a')]),
                mime_type='application/zip'
            )
        self.assertEqual(listing.entries[0]['path'], 'a.txt')


class SVGZTestCase(SimpleTestCase):
    def test_svgz_is_a_drawing(self):
        from mayan.apps.mime_types.refinement import refine_mime_type

        data = io.BytesIO(
            gzip.compress(b'<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg"/>')
        )
        self.assertEqual(
            refine_mime_type(file_object=data, mime_type='application/gzip'),
            'image/svg+xml'
        )
        self.assertEqual(data.tell(), 0)

    def test_other_gzip_file_unchanged(self):
        from mayan.apps.mime_types.refinement import refine_mime_type

        data = io.BytesIO(gzip.compress(b'<html><body>page</body></html>'))
        self.assertEqual(
            refine_mime_type(file_object=data, mime_type='application/gzip'),
            'application/gzip'
        )

    def test_svgz_decompressed_within_a_limit(self):
        from ..backends import python

        drawing = b'<svg xmlns="http://www.w3.org/2000/svg"/>'
        self.assertEqual(python.gunzip_svg(data=gzip.compress(drawing)), drawing)
        with mock.patch.object(python, 'SVGZ_MAXIMUM_SIZE', 1024):
            with self.assertRaises(ValueError):
                python.gunzip_svg(data=gzip.compress(b'<svg>' + b' ' * 4096 + b'</svg>'))
