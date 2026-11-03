"""
Pages drawn by the converter for the formats that have none of their own:
GPS tracks, DICOM objects, audio files; emails rendered without remote
resources; transparency laid over white.
"""
import base64
import http.server
import importlib.util
import io
import math
import shutil
import struct
import tempfile
import threading
import time
import unittest
import wave
from unittest import mock

from PIL import Image

from django.test import SimpleTestCase

from ..backends.python import Python
from ..classes import image_flatten_transparency
from ..exceptions import PageCountError
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
        hint = dicom._decoder_hints()
        self.assertTrue(hint.startswith('install') or hint.startswith('none of'))


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
