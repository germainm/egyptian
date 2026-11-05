"""
Pages drawn by the converter for the formats that have none of their own:
GPS tracks, DICOM objects, audio files; emails rendered without remote
resources, with the images named by their Content-ID and the names of their
attachments; Markdown files without remote resources; transparency laid over
white. The JPEG samples of 12 bits of DICOM objects: test_jpeg_extended.py.
"""
import base64
from email.message import EmailMessage
import http.server
import importlib.util
import io
import math
import shutil
import struct
import subprocess
import tempfile
import threading
import time
import unittest
import wave
from unittest import mock

from PIL import Image
from pypdf import PdfReader
import pypdf

from django.test import SimpleTestCase

from ..backends.python import Python
from ..classes import image_flatten_transparency
from ..exceptions import PageCountError
from mayan.apps.storage.tests.test_outlook import (
    make_compound_file, make_message, text, unicode_stream
)

from ..renderers import dicom, gpx

GPX = b'''<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="tests" xmlns="http://www.topografix.com/GPX/1/1">
  <metadata><name>Balade au Vieux-Port</name></metadata>
  <wpt lat="45.5017" lon="-73.5540"><name>Basilique Notre-Dame</name></wpt>
  <rte><name>Retour</name>
    <rtept lat="45.5075" lon="-73.5513"/><rtept lat="45.5030" lon="-73.5585"/>
  </rte>
  <trk><name>Aller</name><trkseg>
    <trkpt lat="45.5017" lon="-73.5540"><ele>30</ele><time>2026-11-01T14:00:00Z</time></trkpt>
    <trkpt lat="45.5028" lon="-73.5528"><ele>25</ele><time>2026-11-01T14:04:00Z</time></trkpt>
    <trkpt lat="45.5046" lon="-73.5525"><ele>22</ele><time>2026-11-01T14:09:00Z</time></trkpt>
    <trkpt lat="45.5060" lon="-73.5508"><ele>18</ele><time>2026-11-01T14:40:00Z</time></trkpt>
    <trkpt lat="45.5075" lon="-73.5513"><ele>20</ele><time>2026-11-01T14:44:00Z</time></trkpt>
  </trkseg></trk>
</gpx>'''
GPXPY = importlib.util.find_spec('gpxpy') is not None
WEASYPRINT = importlib.util.find_spec('weasyprint') is not None
PYDICOM = importlib.util.find_spec('pydicom') is not None
MARKDOWN = importlib.util.find_spec('markdown') is not None
FFMPEG = bool(shutil.which('ffmpeg') and shutil.which('ffprobe'))


def render_gpx(data=GPX, tile_url=''):
    return gpx.render_gpx_page(
        data=data, tile_url=tile_url, tile_attribution='', maximum_zoom=18,
        user_agent='Egyptian-EDMS tests'
    )


class GPXTestCase(SimpleTestCase):
    def test_page_without_tile_server(self):
        self.assertEqual(render_gpx().size, (gpx.PAGE_WIDTH, gpx.PAGE_HEIGHT))

    def test_unreachable_tile_server(self):
        start = time.monotonic()
        render_gpx(tile_url='http://127.0.0.1:9/{z}/{x}/{y}.png')
        self.assertLess(time.monotonic() - start, 30)

    def test_unknown_placeholder_in_the_tile_address(self):
        render_gpx(tile_url='https://tile.invalid/{z}/{x}/{y}.png?key={apikey}')

    def test_entities_refused(self):
        bomb = (
            b'<?xml version="1.0"?><!DOCTYPE gpx [<!ENTITY a "aaaaaaaaaa">'
            b'<!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">]>'
            b'<gpx version="1.1"><wpt lat="1" lon="1"><name>&b;</name></wpt></gpx>'
        )
        with self.assertRaises(Exception):
            gpx.parse_gpx(data=bomb)

    def test_summary_without_time(self):
        summary = gpx.get_summary(
            gpx=gpx.parse_gpx(
                data=b'<gpx version="1.1"><trk><trkseg><trkpt lat="45.50" lon="-73.55"/>'
                b'<trkpt lat="45.51" lon="-73.55"/></trkseg></trk></gpx>'
            )
        )
        self.assertIsNone(summary['start'])
        self.assertAlmostEqual(summary['distance'], 1112, delta=5)

    def test_route_only(self):
        summary = gpx.get_summary(
            gpx=gpx.parse_gpx(
                data=b'<gpx version="1.1"><rte><rtept lat="45.50" lon="-73.55"/>'
                b'<rtept lat="45.51" lon="-73.55"/></rte></gpx>'
            )
        )
        self.assertEqual(summary['points'], 2)
        self.assertAlmostEqual(summary['distance'], 1112, delta=5)

    @unittest.skipUnless(GPXPY, 'gpxpy not installed')
    def test_figures_of_the_itineraires_app(self):
        import gpxpy

        summary = gpx.get_summary(gpx=gpx.parse_gpx(data=GPX))
        reference = gpxpy.parse(GPX.decode())
        # The tracks only, as the Itinéraires app: not the route.
        self.assertEqual(round(summary['distance']), round(reference.length_3d()))
        self.assertEqual(summary['moving_time'], reference.get_moving_data().moving_time)
        self.assertEqual(summary['points'], 5)

    def test_without_gpxpy(self):
        with mock.patch.dict('sys.modules', {'gpxpy': None, 'gpxpy.gpx': None}):
            summary = gpx.get_summary(gpx=gpx.parse_gpx(data=GPX))
        self.assertIsNone(summary['moving_time'])
        self.assertGreater(summary['distance'], 600)


def make_dicom(photometric='MONOCHROME2', rows=10, columns=10):
    import numpy
    from pydicom.dataset import Dataset, FileMetaDataset
    from pydicom.uid import (
        ExplicitVRLittleEndian, SecondaryCaptureImageStorage, generate_uid
    )

    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    dataset = Dataset()
    dataset.file_meta = meta
    dataset.SOPClassUID = SecondaryCaptureImageStorage
    dataset.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    dataset.PatientName = 'Test^Patient'
    dataset.Modality = 'OT'
    dataset.Rows, dataset.Columns = rows, columns
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = photometric
    dataset.BitsAllocated, dataset.BitsStored, dataset.HighBit = 16, 12, 11
    dataset.PixelRepresentation = 0
    pixels = numpy.arange(rows * columns, dtype=numpy.uint16).reshape(rows, columns) * 40
    dataset.PixelData = pixels.tobytes()
    buffer = io.BytesIO()
    dataset.save_as(buffer, enforce_file_format=True)
    buffer.seek(0)
    return buffer


@unittest.skipUnless(PYDICOM, 'pydicom not installed')
class DICOMTestCase(SimpleTestCase):
    def test_small_image_enlarged(self):
        image = dicom.render_dicom_page(file_object=make_dicom(), page_number=0)
        self.assertEqual(image.size, (520, 520))

    def test_monochrome1_inverted(self):
        normal = dicom.render_dicom_page(file_object=make_dicom(), page_number=0)
        inverted = dicom.render_dicom_page(
            file_object=make_dicom(photometric='MONOCHROME1'), page_number=0
        )
        self.assertLess(normal.getpixel((0, 0)), inverted.getpixel((0, 0)))

    def test_truncated_file(self):
        data = io.BytesIO(b'\x00' * 128 + b'DICM' + b'\x02\x00')
        try:
            pages = Python(file_object=data, mime_type='application/dicom').get_page_count()
        except PageCountError:
            pass
        else:
            self.assertGreaterEqual(pages, 1)

    def test_decoder_hints(self):
        with mock.patch('importlib.util.find_spec', return_value=None):
            hint = dicom._decoder_hints()
        self.assertIn('pyjpegls', hint)
        self.assertIn('pylibjpeg-openjpeg', hint)
        # GPLv3, Apache-2.0: not compatible with the license of this project.
        self.assertNotIn('pylibjpeg-libjpeg', hint)
        self.assertNotIn('gdcm', hint)

        with mock.patch('importlib.util.find_spec', return_value=object()):
            self.assertEqual(
                dicom._decoder_hints(),
                'none of the installed decoders reads this file'
            )

    def _assert_same_page_as_uncompressed(self, name):
        from pydicom.data import get_testdata_file

        pages = []
        for file_name in ('MR_small.dcm', name):
            path = get_testdata_file(file_name, download=False)
            if not path:
                self.skipTest('sample file of pydicom not installed')
            with open(path, mode='rb') as file_object:
                pages.append(
                    dicom.render_dicom_page(
                        file_object=file_object, page_number=0
                    ).tobytes()
                )
        self.assertEqual(pages[0], pages[1])

    @unittest.skipUnless(
        importlib.util.find_spec('jpeg_ls'), 'pyjpegls not installed'
    )
    def test_jpeg_ls(self):
        self._assert_same_page_as_uncompressed('MR_small_jpeg_ls_lossless.dcm')

    @unittest.skipUnless(
        importlib.util.find_spec('openjpeg'), 'pylibjpeg-openjpeg not installed'
    )
    def test_jpeg_2000(self):
        self._assert_same_page_as_uncompressed('MR_small_jp2klossless.dcm')

    def test_rle(self):
        self._assert_same_page_as_uncompressed('MR_small_RLE.dcm')


@unittest.skipUnless(FFMPEG, 'ffmpeg and ffprobe not installed')
class AudioTestCase(SimpleTestCase):
    def test_wav_page(self):
        with tempfile.NamedTemporaryFile(suffix='.wav') as file:
            with wave.open(file.name, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(8000)
                wav.writeframes(
                    b''.join(
                        struct.pack('<h', int(8000 * math.sin(index / 5)))
                        for index in range(8000)
                    )
                )
            with open(file.name, 'rb') as file_object:
                converter = Python(file_object=file_object, mime_type='audio/x-wav')
                self.assertEqual(converter.get_page_count(), 1)
                converter.seek_page(page_number=0)
                self.assertEqual(converter.image.size, (1600, 1200))


def png_bytes(color=(0, 160, 0)):
    buffer = io.BytesIO()
    Image.new('RGB', (40, 40), color).save(buffer, 'PNG')
    return buffer.getvalue()


def count_green(image):
    return sum(
        1 for pixel in image.getdata()
        if pixel[1] > 120 and pixel[0] < 80 and pixel[2] < 80
    )


class RecordingHandler(http.server.BaseHTTPRequestHandler):
    requests = []

    def do_GET(self):
        RecordingHandler.requests.append(self.path)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'body{background:red}')

    def log_message(self, *args):
        pass


@unittest.skipUnless(WEASYPRINT, 'WeasyPrint not installed')
class EmailTestCase(SimpleTestCase):
    def test_no_remote_resource_and_data_images_kept(self):
        server = http.server.HTTPServer(('127.0.0.1', 0), RecordingHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        port = server.server_address[1]
        buffer = io.BytesIO()
        Image.new('RGB', (40, 40), (0, 160, 0)).save(buffer, 'PNG')
        email = (
            'From: a@example.com\r\nTo: b@example.com\r\nSubject: Essai\r\n'
            'MIME-Version: 1.0\r\nContent-Type: text/html; charset=utf-8\r\n\r\n'
            '<html><head><link rel="stylesheet" href="http://127.0.0.1:{port}/s.css">'
            '</head><body><p>Corps</p><img src="http://127.0.0.1:{port}/p.png">'
            '<img src="file:///etc/hostname"><img src="data:image/png;base64,{data}">'
            '</body></html>'
        ).format(port=port, data=base64.b64encode(buffer.getvalue()).decode()).encode()
        try:
            RecordingHandler.requests = []
            converter = Python(file_object=io.BytesIO(email), mime_type='message/rfc822')
            converter.get_page_count()
            converter.seek_page(page_number=0)
            image = converter.image.convert('RGB')
        finally:
            server.shutdown()
        self.assertEqual(RecordingHandler.requests, [])
        green = sum(
            1 for pixel in image.getdata()
            if pixel[1] > 120 and pixel[0] < 80 and pixel[2] < 80
        )
        self.assertGreater(green, 100)

    def test_long_email_on_several_pages(self):
        body = '\n'.join(
            'Ligne {} du long courriel, avec un < et un &.'.format(index)
            for index in range(400)
        )
        email = (
            'Return-Path: <a@example.com>\nFrom: a@example.com\nTo: b@example.com\n'
            'Subject: Long\nContent-Type: text/plain; charset=utf-8\n\n' + body
        ).encode()
        pages = Python(file_object=io.BytesIO(email), mime_type='message/rfc822').get_page_count()
        self.assertGreater(pages, 1)
        converter = Python(file_object=io.BytesIO(email), mime_type='message/rfc822')
        converter.seek_page(page_number=pages - 1)
        self.assertIsNotNone(converter.image)


    def _render_email(self, email):
        converter = Python(file_object=io.BytesIO(email), mime_type='message/rfc822')
        converter.get_page_count()
        converter.seek_page(page_number=0)
        return converter.image.convert('RGB')

    def _pdf_text(self, email):
        converter = Python(file_object=io.BytesIO(email), mime_type='message/rfc822')
        with converter.to_pdf() as file_object:
            reader = pypdf.PdfReader(file_object)
            return ' '.join(page.extract_text() for page in reader.pages)

    def test_image_named_by_its_content_id(self):
        message = EmailMessage()
        message['From'] = 'a@example.com'
        message['Subject'] = 'Image'
        message.set_content('Texte')
        message.add_alternative(
            '<p>Corps</p><img src="cid:image1@example.com" width="200">',
            subtype='html'
        )
        message.get_payload()[1].add_related(
            png_bytes(), 'image', 'png', cid='<image1@example.com>',
            filename='image1.png'
        )
        email = message.as_bytes()
        self.assertGreater(count_green(self._render_email(email)), 1000)
        self.assertNotIn('image1.png', self._pdf_text(email))

    def test_attachments_named_cc_and_body_of_the_message(self):
        attached = EmailMessage()
        attached['Subject'] = 'Message joint'
        attached.add_alternative('<p>Corps du message joint</p>', subtype='html')

        message = EmailMessage()
        message['From'] = 'a@example.com'
        message['To'] = 'b@example.com'
        message['Cc'] = 'c@example.com'
        message['Subject'] = 'Pieces'
        message.set_content('Corps du message')
        message.add_attachment(
            b'x' * 3000, maintype='application', subtype='pdf',
            filename='rapport.pdf'
        )
        message.add_attachment(attached)
        text = self._pdf_text(message.as_bytes())
        self.assertIn('c@example.com', text)
        self.assertIn('Corps du message', text)
        self.assertIn('rapport.pdf (3 Ko)', text)
        self.assertIn('Message joint', text)
        # The attached message was taken for the body.
        self.assertNotIn('Corps du message joint', text)

    def test_alternative_text_not_named_as_attachment(self):
        message = EmailMessage()
        message['Subject'] = 'Sujet'
        message.set_content('Version texte')
        message.add_alternative('<p>Version HTML</p>', subtype='html')
        text = self._pdf_text(message.as_bytes())
        self.assertIn('Version HTML', text)
        self.assertNotIn('Version texte', text)
        self.assertNotIn('Pièces jointes', text)

    def test_unknown_content_id_stays_blocked(self):
        email = (
            'From: a@example.com\r\nSubject: Essai\r\nMIME-Version: 1.0\r\n'
            'Content-Type: text/html; charset=utf-8\r\n\r\n'
            '<p>Corps</p><img src="cid:absent@example.com">'
        ).encode()
        self.assertIn('Corps', self._pdf_text(email))

    def test_attachment_alone(self):
        email = (
            'From: a@example.com\r\nSubject: Essai\r\nMIME-Version: 1.0\r\n'
            'Content-Type: application/pdf; name=seul.pdf\r\n'
            'Content-Disposition: attachment; filename=seul.pdf\r\n\r\nxxx'
        ).encode()
        self.assertIn('seul.pdf', self._pdf_text(email))


@unittest.skipUnless(WEASYPRINT and MARKDOWN, 'WeasyPrint or Markdown not installed')
class MarkdownTestCase(SimpleTestCase):
    def test_remote_and_local_resources_not_loaded(self):
        server = http.server.HTTPServer(('127.0.0.1', 0), RecordingHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        port = server.server_address[1]
        address = 'http://127.0.0.1:{}'.format(port)
        with tempfile.NamedTemporaryFile(suffix='.png') as local_file:
            local_file.write(png_bytes(color=(200, 0, 0)))
            local_file.flush()
            text = (
                '# Titre\n\nCorps du fichier.\n\n'
                '![distante]({address}/p.png)\n\n'
                '<link rel="stylesheet" href="{address}/s.css">\n\n'
                '<style>@import "{address}/i.css";'
                '@font-face {{font-family: x; src: url({address}/f.woff)}}'
                'body {{background: url({address}/b.png)}}</style>\n\n'
                '<link rel="attachment" href="{address}/a.txt">\n\n'
                '<img src="{address}/h.png"><img src="file://{local}" width="200">'
                '<img src="data:image/png;base64,{data}" width="200">\n'
            ).format(
                address=address, local=local_file.name,
                data=base64.b64encode(png_bytes()).decode()
            ).encode()
            try:
                RecordingHandler.requests = []
                converter = Python(
                    file_object=io.BytesIO(text), mime_type='text/markdown'
                )
                self.assertGreaterEqual(converter.get_page_count(), 1)
                converter.seek_page(page_number=0)
                image = converter.image.convert('RGB')
            finally:
                server.shutdown()

        self.assertEqual(RecordingHandler.requests, [])
        self.assertGreater(count_green(image), 1000)
        red = sum(
            1 for pixel in image.getdata()
            if pixel[0] > 150 and pixel[1] < 60 and pixel[2] < 60
        )
        self.assertEqual(red, 0)

    def test_page_count_of_a_long_file(self):
        text = '\n\n'.join('Paragraphe {}'.format(index) for index in range(300))
        converter = Python(file_object=io.BytesIO(text.encode()), mime_type='text/markdown')
        self.assertGreater(converter.get_page_count(), 1)


@unittest.skipUnless(
    WEASYPRINT and shutil.which('pdftotext'), 'WeasyPrint or pdftotext not installed'
)
class OutlookMessageTestCase(SimpleTestCase):
    def get_text(self, file_object):
        converter = Python(
            file_object=file_object, mime_type='application/vnd.ms-outlook'
        )
        with converter.to_pdf() as pdf_file_object:
            return subprocess.run(
                ('pdftotext', pdf_file_object.name, '-'), capture_output=True,
                check=True
            ).stdout.decode()

    def test_page_with_the_headers(self):
        text = self.get_text(file_object=make_message())
        for expected in (
            'alice@example.com', 'bob@example.com', 'carol@example.com',
            'dan@example.com', 'Facture été', 'Le corps', 'du message.',
            'facture.pdf', 'COURT.TXT'
        ):
            self.assertIn(expected, text)
        # A blind copy is not in the headers of a message.
        self.assertNotIn('eve@example.com', text)

    def test_html_of_outlook_on_the_page_of_the_headers(self):
        html = (
            b'<html><head><style>@page WordSection1 {size: 8.5in 11in;} '
            b'div.WordSection1 {page: WordSection1;}</style></head><body>'
            b'<div class=WordSection1><p>Corps du message HTML</p></div>'
            b'</body></html>'
        )
        converter = Python(
            file_object=make_message(**{'__substg1.0_10130102': html}),
            mime_type='application/vnd.ms-outlook'
        )
        with converter.to_pdf() as pdf_file_object:
            reader = PdfReader(pdf_file_object.name)
            text = subprocess.run(
                ('pdftotext', '-f', '1', '-l', '1', pdf_file_object.name, '-'),
                capture_output=True, check=True
            ).stdout.decode()
        self.assertEqual(len(reader.pages), 1)
        self.assertIn('alice@example.com', text)
        self.assertIn('Corps du message HTML', text)
        # A4, not the size that the message asks for.
        self.assertAlmostEqual(float(reader.pages[0].mediabox.width), 595.3, delta=1)

    def test_images_named_by_the_html_body(self):
        buffer = io.BytesIO()
        Image.new('RGB', (40, 40), (0, 160, 0)).save(buffer, 'PNG')
        converter = Python(
            file_object=make_message(
                **{
                    '__substg1.0_10130102': b'<p>HTML</p><img src="cid:image@x">',
                    '__attach_version1.0_#00000001': {
                        unicode_stream(0x3707): text('image.png'),
                        unicode_stream(0x3712): text('image@x'),
                        '__substg1.0_37010102': buffer.getvalue()
                    }
                }
            ), mime_type='application/vnd.ms-outlook'
        )
        with converter.to_pdf() as pdf_file_object:
            pdf = pdf_file_object.read()
        image = converter._pdf_bytes_to_image(pdf, page_number=0).convert('RGB')
        green = sum(
            1 for pixel in image.getdata()
            if pixel[1] > 120 and pixel[0] < 80 and pixel[2] < 80
        )
        self.assertGreater(green, 100)

    def test_other_compound_file_keeps_its_path(self):
        file_object = io.BytesIO(make_compound_file({'WordDocument': b'x' * 100}))
        converter = Python(
            file_object=file_object, mime_type='application/x-ole-storage'
        )
        self.assertIsNone(converter._get_msg_as_eml())
        self.assertEqual(file_object.tell(), 0)

    def test_file_left_at_its_start(self):
        file_object = make_message()
        converter = Python(
            file_object=file_object, mime_type='application/vnd.ms-outlook'
        )
        self.assertTrue(converter._get_msg_as_eml())
        self.assertEqual(file_object.tell(), 0)


class TransparencyTestCase(SimpleTestCase):
    def test_opaque_image_unchanged(self):
        image = Image.new('RGB', (10, 10), (10, 20, 30))
        self.assertIs(image_flatten_transparency(image), image)

    def test_transparent_images_over_white(self):
        rgba = Image.new('RGBA', (10, 10), (0, 0, 0, 0))
        self.assertEqual(image_flatten_transparency(rgba).getpixel((0, 0)), (255, 255, 255))
        palette = Image.new('P', (10, 10), 0)
        palette.info['transparency'] = 0
        self.assertEqual(image_flatten_transparency(palette).getpixel((0, 0)), (255, 255, 255))
        grey = Image.new('LA', (10, 10), (0, 128))
        self.assertTrue(
            all(abs(value - 127) <= 1 for value in image_flatten_transparency(grey).getpixel((0, 0)))
        )
