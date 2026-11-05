"""
The image of a signature, from its drawing given as a data: URL.
"""
import base64
import os
import unittest

from django.test import SimpleTestCase

from mayan.apps.converter.renderers import svg

from ..model_mixins import SignatureCaptureBusinessLogicMixin

READY = os.path.exists(svg.get_rsvg_convert_path())


class Signature(SignatureCaptureBusinessLogicMixin):
    def __init__(self, data):
        self.svg = data


@unittest.skipUnless(READY, 'rsvg-convert not installed')
class ImageTestCase(SimpleTestCase):
    def test_image_of_the_drawing(self):
        # As the widget gives them.
        drawing = (
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 200" '
            'width="400" height="200"><path d="M 10 10 L 390 190" '
            'stroke-width="3" stroke="rgb(0,0,0)" fill="none"/></svg>'
        )
        image = Signature(
            data='data:image/svg+xml;base64,{}'.format(
                base64.b64encode(drawing.encode()).decode()
            )
        ).get_image()
        self.assertEqual(image.size, (400, 200))
        self.assertEqual(image.convert('RGBA').getpixel((200, 100))[3], 255)

    def test_other_address_refused(self):
        with self.assertRaises(svg.SVGRenderError):
            Signature(data='file:///etc/hostname').get_image()
