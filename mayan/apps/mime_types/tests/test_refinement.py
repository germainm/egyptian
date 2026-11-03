"""
MIME types refined from the content of the file when file(1) gives a
generic one: Office Open XML, OpenDocument and EPUB in ZIP files, DICOM and
raw photos in TIFF files, EMF and RW2 in octet streams, GPS tracks in XML
files, emails in text files, SVG drawings in gzip files.
"""
import gzip
import io
import struct
import zipfile

from django.test import SimpleTestCase

from ..refinement import refine_mime_type


def refine(data, mime_type):
    file_object = io.BytesIO(data)
    result = refine_mime_type(file_object=file_object, mime_type=mime_type)
    return result


def make_zip(members):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        for name, data in members:
            zip_file.writestr(name, data)
    return buffer.getvalue()


def make_tiff(tags, make=b''):
    """Little-endian TIFF with one IFD: (tag, type, value) entries."""
    entries = []
    make_offset = 8 + 2 + 12 * (len(tags) + (1 if make else 0)) + 4
    for tag, field_type, value in tags:
        entries.append(struct.pack('<HHI4s', tag, field_type, 1, struct.pack('<I', value)))
    if make:
        entries.append(
            struct.pack('<HHII', 271, 2, len(make) + 1, make_offset)
        )
    ifd = struct.pack('<H', len(entries)) + b''.join(entries) + b'\x00' * 4
    return b'II*\x00' + struct.pack('<I', 8) + ifd + make + b'\x00'


class ZipTestCase(SimpleTestCase):
    def test_docx_without_content_types_first(self):
        data = make_zip(
            [('word/document.xml', '<w/>'), ('[Content_Types].xml', '<Types/>')]
        )
        self.assertEqual(
            refine(data, 'application/zip'),
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    def test_xlsx_and_pptx(self):
        self.assertTrue(
            refine(
                make_zip([('[Content_Types].xml', ''), ('xl/workbook.xml', '')]),
                'application/zip'
            ).endswith('spreadsheetml.sheet')
        )
        self.assertTrue(
            refine(
                make_zip([('[Content_Types].xml', ''), ('ppt/presentation.xml', '')]),
                'application/zip'
            ).endswith('presentationml.presentation')
        )

    def test_opendocument_mimetype_member(self):
        data = make_zip(
            [('mimetype', 'application/vnd.oasis.opendocument.formula'), ('content.xml', '')]
        )
        self.assertEqual(
            refine(data, 'application/zip'),
            'application/vnd.oasis.opendocument.formula'
        )

    def test_untrusted_mimetype_member(self):
        data = make_zip([('mimetype', 'text/html')])
        self.assertEqual(refine(data, 'application/zip'), 'application/zip')

    def test_epub_container(self):
        data = make_zip([('META-INF/container.xml', '<container/>')])
        self.assertEqual(refine(data, 'application/zip'), 'application/epub+zip')

    def test_plain_archive(self):
        data = make_zip([('a.txt', 'a')])
        self.assertEqual(refine(data, 'application/zip'), 'application/zip')


class TiffTestCase(SimpleTestCase):
    def test_dicom_with_a_tiff_header(self):
        data = b'II*\x00' + bytes(124) + b'DICM' + bytes(64)
        self.assertEqual(refine(data, 'image/tiff'), 'application/dicom')

    def test_raw_photo_by_make(self):
        data = make_tiff(tags=[(254, 4, 1)], make=b'NIKON CORPORATION')
        self.assertEqual(refine(data, 'image/tiff'), 'image/x-nikon-nef')

    def test_dng(self):
        data = make_tiff(tags=[(50706, 1, 0)])
        self.assertEqual(refine(data, 'image/tiff'), 'image/x-adobe-dng')

    def test_ordinary_tiff(self):
        data = make_tiff(tags=[(254, 4, 0)], make=b'NIKON CORPORATION')
        self.assertEqual(refine(data, 'image/tiff'), 'image/tiff')


class OctetStreamTestCase(SimpleTestCase):
    def test_emf(self):
        data = b'\x01\x00\x00\x00' + bytes(36) + b' EMF' + bytes(40)
        self.assertEqual(refine(data, 'application/octet-stream'), 'image/emf')

    def test_panasonic_raw(self):
        data = b'IIU\x00' + bytes(60)
        self.assertEqual(
            refine(data, 'application/octet-stream'), 'image/x-panasonic-rw2'
        )

    def test_dicom(self):
        data = bytes(128) + b'DICM' + bytes(16)
        self.assertEqual(refine(data, 'application/octet-stream'), 'application/dicom')

    def test_unknown(self):
        self.assertEqual(
            refine(b'\x00\x01\x02' * 30, 'application/octet-stream'),
            'application/octet-stream'
        )


class GPXTestCase(SimpleTestCase):
    def test_cases(self):
        cases = {
            b'<?xml version="1.0"?>\n<!-- <gpx> -->\n<gpxdata/>': 'text/xml',
            b'<?xml version="1.0"?>\n<gpx:gpx xmlns:gpx="http://www.topografix.com/GPX/1/1"/>': 'application/gpx+xml',
            b'\xef\xbb\xbf<gpx version="1.1"></gpx>': 'application/gpx+xml',
            b'<html><body>gpx</body></html>': 'text/xml',
            b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY e "<gpx>">]><root/>': 'text/xml',
            b'<!DOCTYPE gpx><?pi x?><gpx version="1.1"/>': 'application/gpx+xml',
            '<!-- non fermé <gpx>'.encode(): 'text/xml',
        }
        for data, expected in cases.items():
            with self.subTest(data=data):
                self.assertEqual(refine(data, 'text/xml'), expected)

    def test_gpx_reported_as_text(self):
        self.assertEqual(
            refine(b'<gpx version="1.1"/>', 'text/plain'), 'application/gpx+xml'
        )


class EmailTestCase(SimpleTestCase):
    def test_cases(self):
        cases = {
            'ordinary note': (b'Titre: Mes notes\nDate: 2026-01-01\nAuteur: moi\n\nTexte.\n', 'text/plain'),
            'list of keys': (b'nom: valeur\ncle: autre\nTo: quelqu-un\n\nsuite\n', 'text/plain'),
            'no blank line': (b'From: a\nTo: b\nSubject: c\n' * 2000, 'text/plain'),
            'sent memo': (b'From: a@x\nTo: b@y\nSubject: Note\n\nCorps\n', 'message/rfc822'),
            'mbox': (
                b'From a@x Tue Nov  3 08:00:00 2026\nReceived: x\nFrom: a@x\nSubject: s\n\nCorps\n',
                'message/rfc822'
            ),
            'free text': ('Bonjour,\nceci est un texte : il a des deux-points.\n\nFin.\n'.encode(), 'text/plain'),
        }
        for name, (data, expected) in cases.items():
            with self.subTest(name=name):
                self.assertEqual(refine(data, 'text/plain'), expected)


class GzipTestCase(SimpleTestCase):
    def test_svgz(self):
        data = gzip.compress(b'<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg"/>')
        self.assertEqual(refine(data, 'application/gzip'), 'image/svg+xml')

    def test_other_gzip(self):
        self.assertEqual(
            refine(gzip.compress(b'just text'), 'application/gzip'), 'application/gzip'
        )

    def test_position_restored(self):
        file_object = io.BytesIO(make_zip([('word/document.xml', ''), ('[Content_Types].xml', '')]))
        file_object.seek(5)
        refine_mime_type(file_object=file_object, mime_type='application/zip')
        self.assertEqual(file_object.tell(), 5)
