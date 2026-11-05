"""
Drawings of the SVG files, by rsvg-convert: what the converter shows, and what a
file cannot make it do.
"""
import base64
import gzip
import http.server
import io
import os
import tempfile
import threading
import time
import unittest
from unittest import mock

from PIL import Image

from django.test import SimpleTestCase

from ..backends import python
from ..backends.python import Python
from ..renderers import svg
from ..renderers.svg import SVGRenderError, render_svg, render_svg_data_url

READY = os.path.exists(svg.get_rsvg_convert_path())
NAMESPACES = (
    'xmlns="http://www.w3.org/2000/svg" '
    'xmlns:xlink="http://www.w3.org/1999/xlink"'
)
DRAWING = (
    '<svg {} width="60" height="40"><rect width="30" height="40" fill="#ff0000"/>'
    '</svg>'
).format(NAMESPACES).encode()


class RecordingHandler(http.server.BaseHTTPRequestHandler):
    requests = []

    def do_GET(self):
        RecordingHandler.requests.append(self.path)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(DRAWING)

    def log_message(self, *args):
        pass


@unittest.skipUnless(READY, 'rsvg-convert not installed')
class RenderTestCase(SimpleTestCase):
    def test_size_colors_and_transparency(self):
        image = render_svg(data=DRAWING).convert('RGBA')
        self.assertEqual(image.size, (60, 40))
        self.assertEqual(image.getpixel((10, 10)), (255, 0, 0, 255))
        self.assertEqual(image.getpixel((50, 10))[3], 0)

    def test_view_box_gives_the_size(self):
        image = render_svg(
            data='<svg {} viewBox="0 0 300 200"/>'.format(NAMESPACES).encode()
        )
        self.assertEqual(image.size, (300, 200))

    def test_page_of_the_converter(self):
        converter = Python(
            file_object=io.BytesIO(DRAWING), mime_type='image/svg+xml'
        )
        self.assertEqual(converter.get_page_count(), 1)
        converter.seek_page(page_number=0)
        self.assertEqual(converter.image.size, (60, 40))
        self.assertEqual(
            converter.image.convert('RGB').getpixel((10, 10)), (255, 0, 0)
        )

    def test_compressed_drawing_decompressed_within_its_limit(self):
        converter = Python(
            file_object=io.BytesIO(gzip.compress(DRAWING)),
            mime_type='image/svg+xml'
        )
        with mock.patch.object(
            python, 'gunzip_svg', wraps=python.gunzip_svg
        ) as mocked:
            converter.seek_page(page_number=0)
        mocked.assert_called_once()
        self.assertEqual(converter.image.size, (60, 40))

    def test_files_refused(self):
        for name, data in (
            ('empty', b''), ('text', b'bonjour'),
            ('other XML', b'<?xml version="1.0"?><a/>'),
            ('no size', '<svg {} width="0" height="0"/>'.format(NAMESPACES).encode()),
            ('too large', '<svg {} width="99999" height="99999"/>'.format(NAMESPACES).encode())
        ):
            with self.subTest(name=name):
                with self.assertRaises(SVGRenderError):
                    render_svg(data=data)

    def test_program_not_installed(self):
        with mock.patch.object(
            svg, 'get_rsvg_convert_path', return_value='/inexistant/rsvg-convert'
        ):
            with self.assertRaises(SVGRenderError):
                render_svg(data=DRAWING)
            with mock.patch.object(
                svg.shutil, 'which', return_value=None
            ), self.assertRaisesRegex(SVGRenderError, 'not installed'):
                render_svg(data=DRAWING)


@unittest.skipUnless(READY, 'rsvg-convert not installed')
class LimitsTestCase(SimpleTestCase):
    def test_huge_drawing_refused_quickly(self):
        start = time.monotonic()
        with self.assertRaises(SVGRenderError):
            render_svg(
                data=(
                    '<svg {0} width="32000" height="32000"><rect width="100%" '
                    'height="100%" fill="red"/></svg>'
                ).format(NAMESPACES).encode()
            )
        self.assertLess(time.monotonic() - start, 10)

    def test_large_drawing_within_the_limit(self):
        image = render_svg(
            data='<svg {} width="4000" height="4000"/>'.format(NAMESPACES).encode()
        )
        self.assertEqual(image.size, (4000, 4000))

    def test_time_limit(self):
        with mock.patch.object(svg, 'TIME_MAXIMUM', new=0.001):
            with self.assertRaisesRegex(SVGRenderError, 'seconds'):
                render_svg(data=DRAWING)

    def test_recursive_references(self):
        groups = ''.join(
            '<g id="g{0}"><use xlink:href="#g{1}"/><use xlink:href="#g{1}"/></g>'.format(
                index, index + 1
            ) for index in range(40)
        )
        start = time.monotonic()
        with self.assertRaises(SVGRenderError):
            render_svg(
                data=(
                    '<svg {} width="50" height="50"><defs>{}<g id="g40"/></defs>'
                    '<use xlink:href="#g0"/></svg>'
                ).format(NAMESPACES, groups).encode()
            )
        self.assertLess(time.monotonic() - start, 30)

    def test_entities(self):
        expansion = '<!ENTITY a "aaaaaaaaaa">' + ''.join(
            '<!ENTITY {} "{}">'.format(
                chr(98 + index), ('&' + chr(97 + index) + ';') * 10
            ) for index in range(9)
        )
        for name, doctype, body in (
            ('expansion', expansion, '&j;'),
            ('file', '<!ENTITY x SYSTEM "file:///etc/hostname">', '&x;')
        ):
            with self.subTest(name=name), self.assertRaises(SVGRenderError):
                render_svg(
                    data=(
                        '<!DOCTYPE svg [{}]><svg {} width="50" height="50">'
                        '<text y="20">{}</text></svg>'
                    ).format(doctype, NAMESPACES, body).encode()
                )


@unittest.skipUnless(READY, 'rsvg-convert not installed')
class ExternalResourcesTestCase(SimpleTestCase):
    def setUp(self):
        self.server = http.server.HTTPServer(('127.0.0.1', 0), RecordingHandler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        RecordingHandler.requests = []
        self.url = 'http://127.0.0.1:{}'.format(self.server.server_address[1])

    def test_no_request(self):
        url = self.url
        for name, body, before in (
            ('image', '<image href="{}/a.png" width="50" height="50"/>'.format(url), ''),
            ('use', '<use xlink:href="{}/a.svg#a"/>'.format(url), ''),
            ('style', '<style>@import url("{}/s.css");</style>'.format(url), ''),
            (
                'filter', '<filter id="f"><feImage href="{}/f.png"/></filter>'
                '<rect width="9" height="9" filter="url(#f)"/>'.format(url), ''
            ),
            (
                'include', '<xi:include xmlns:xi="http://www.w3.org/2001/XInclude" '
                'href="{}/i.xml"/>'.format(url), ''
            ),
            (
                'style sheet', '', '<?xml-stylesheet href="{}/x.css" '
                'type="text/css"?>'.format(url)
            )
        ):
            with self.subTest(name=name):
                render_svg(
                    data='{}<svg {} width="50" height="50">{}</svg>'.format(
                        before, NAMESPACES, body
                    ).encode()
                )
        self.assertEqual(RecordingHandler.requests, [])

    def test_no_file_of_the_server(self):
        with tempfile.NamedTemporaryFile(suffix='.svg') as file_object:
            file_object.write(DRAWING)
            file_object.flush()
            for body in (
                '<image xlink:href="file://{}" width="50" height="50"/>',
                '<use xlink:href="file://{}#a"/>'
            ):
                with self.subTest(body=body):
                    image = render_svg(
                        data='<svg {} width="50" height="50">{}</svg>'.format(
                            NAMESPACES, body.format(file_object.name)
                        ).encode()
                    ).convert('RGBA')
                    self.assertEqual(image.getextrema()[3], (0, 0))


@unittest.skipUnless(READY, 'rsvg-convert not installed')
class DataURLTestCase(SimpleTestCase):
    def test_encodings(self):
        for name, url in (
            (
                'base64', 'data:image/svg+xml;base64,{}'.format(
                    base64.b64encode(DRAWING).decode()
                )
            ),
            ('text', 'data:image/svg+xml,{}'.format(DRAWING.decode().replace('#', '%23'))),
            (
                'charset', 'data:image/svg+xml;charset=utf-8,{}'.format(
                    DRAWING.decode().replace('#', '%23')
                )
            )
        ):
            with self.subTest(name=name):
                image = render_svg_data_url(url=url).convert('RGBA')
                self.assertEqual(image.size, (60, 40))
                self.assertEqual(image.getpixel((10, 10)), (255, 0, 0, 255))

    def test_nothing_else_is_read(self):
        server = http.server.HTTPServer(('127.0.0.1', 0), RecordingHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        RecordingHandler.requests = []
        for url in (
            'http://127.0.0.1:{}/a.svg'.format(server.server_address[1]),
            'file:///etc/hostname', '/etc/hostname', '', 'bonjour',
            'data:image/png;base64,AAAA', 'data:text/plain,bonjour',
            'file:///etc/hostname,{}'.format(DRAWING.decode())
        ):
            with self.subTest(url=url), self.assertRaisesRegex(
                SVGRenderError, 'Not the data: URL'
            ):
                render_svg_data_url(url=url)
        with self.assertRaises(SVGRenderError):
            render_svg_data_url(url='data:image/svg+xml;base64,@@@')
        self.assertEqual(RecordingHandler.requests, [])
