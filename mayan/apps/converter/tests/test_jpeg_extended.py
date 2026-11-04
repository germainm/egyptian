"""
Decoder of the sequential JPEG images with samples of 12 bits. The expected
values come from libjpeg-turbo 3.1.3, which made the images of these tests:
this project does not depend on it.
"""
import base64
import hashlib
import importlib.util
import io
import unittest
from unittest import mock

from PIL import Image

from django.test import SimpleTestCase

from ..renderers import dicom, jpeg_extended

PYDICOM = importlib.util.find_spec('pydicom') is not None

# A ramp of 24 by 16 pixels from 0 to 4095.
JPEG_12_BITS = base64.b64decode((
    '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAIBAQEBAQIBAQECAgICAgQDAgICAgUEBAMEBg'
    'UGBgYFBgYGBwkIBgcJBwYGCAsICQoKCgoKBggLDAsKDAkKCgr/wQALDAAQABgBAREA/8QA'
    'FQABAQAAAAAAAAAAAAAAAAAADA3/xAAbEAABBAMAAAAAAAAAAAAAAAALACg3RVRicv/aAA'
    'gBAQAAPwCXjAUwKcMMywKDjVNeQKYFOGGY4FBxqmvAFMCnDDMcCg41QocCmBThhmOBQcap'
    'rwBTApwwzHAoONU15ApgU4YZjgUHGq//2Q=='
))
JPEG_12_BITS_SHA256 = '1548f9360609bfa4045ed251ebd67927afb777a621c9d195e4f60336cb231f77'
# The ramp inverted, for a second frame.
JPEG_12_BITS_INVERTED = base64.b64decode((
    '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAIBAQEBAQIBAQECAgICAgQDAgICAgUEBAMEBg'
    'UGBgYFBgYGBwkIBgcJBwYGCAsICQoKCgoKBggLDAsKDAkKCgr/wQALDAAQABgBAREA/8QA'
    'FQABAQAAAAAAAAAAAAAAAAAADA3/xAAbEAABBAMAAAAAAAAAAAAAAAALACg3RVRicv/aAA'
    'gBAQAAPwCoanrD1kzvNz7/AL2QoY9Yesmd52ff97IUOesPWTO87Pv+9k14PWHrJnedn3/e'
    'yFDnrD1kzvOz7/vZChj1h6yZ3nZ9/wB7L//Z'
))
JPEG_12_BITS_INVERTED_SHA256 = '974e8fccf4f4bc9be93bd628d8d20e75ff2aba33da5e3539818c3cb77bdbc6c3'
# The ramp in RGB, stored in YCbCr with all the samples.
JPEG_12_BITS_COLOR = base64.b64decode((
    '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAIBAQEBAQIBAQECAgICAgQDAgICAgUEBAMEBg'
    'UGBgYFBgYGBwkIBgcJBwYGCAsICQoKCgoKBggLDAsKDAkKCgr/2wBDAQICAgICAgUDAwUK'
    'BwYHCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCg'
    'r/wQARDAAQABgDAREAAhEBAxEB/8QAFgABAQEAAAAAAAAAAAAAAAAADAsN/8QAHhAAAAYD'
    'AQEAAAAAAAAAAAAAAAoLN0RUJ2FyARf/xAAWAQEBAQAAAAAAAAAAAAAAAAAMCg3/xAAiEQ'
    'AAAgoDAAAAAAAAAAAAAAAACggJJCYzNkJDUVNhcuL/2gAMAwEAAhEDEQA/AIJSQmcWbD36'
    'nTmc7D8A+stLmlu3VduQcRRfIUwHWxZ8hTOkJnFWwynTmc7Aoc+stLmlu3VduRRkjAQpgO'
    'tiz5CmZITOLNhlOnM52BQ59ZaXNLduq7cijBGAhTAdbFnyMXISEzirYZSpzOdjWZD6y0ua'
    'W7dV25CRZF8hTAdbFnyFMyQmcWbDKdOZzsChz6y0uaW7dV25FGSMBCmA62LPkKZ0hM4q2G'
    'U6cznYFDH1lpc0t26rtyKMEYCFMB1sWfI//9k='
))
JPEG_12_BITS_COLOR_RGB_SHA256 = '20a2df959e7cd757bd7f11601f7f8f61b70edd46d7caf6dbbfe5d20bd5349602'
JPEG_12_BITS_COLOR_SHA256 = '4fb1aa5d8355e405e213b06b81bac8a0a3a52e6856568362a74c76b6f733f59f'
# The same with half of the chroma samples: the luma is compared.
JPEG_12_BITS_SUBSAMPLED = base64.b64decode((
    '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAIBAQEBAQIBAQECAgICAgQDAgICAgUEBAMEBg'
    'UGBgYFBgYGBwkIBgcJBwYGCAsICQoKCgoKBggLDAsKDAkKCgr/2wBDAQICAgICAgUDAwUK'
    'BwYHCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCg'
    'r/wQARDAAQABgDASIAAhEBAxEB/8QAFgABAQEAAAAAAAAAAAAAAAAADAAL/8QAHhAAAAYD'
    'AQEAAAAAAAAAAAAAAAoLN0RUJ2FyARf/xAAXAQADAQAAAAAAAAAAAAAAAAAJCgsN/8QAKx'
    'EAAAEHCwUAAAAAAAAAAAAAAAoLJSdDUmEBAwQGCAkpNDdEYlRjcXKk/9oADAMBAAIRAxEA'
    'PwDBKSEzizYe/U6cznYUzpCZxVsMp05nOwAuSEzirYZSpzOdhTMkJnFmwynTmc7Fr4/WFS'
    '2qSc6xp7xA5rr8wp5JVruz8cA/RSEzizYZTpzOdiGUqkJnFWwynTmc7EMjYLdCpfHhrunH'
    'mnfnYh8SzeYU1Y0ZVvxwk4D/2Q=='
))
JPEG_12_BITS_SUBSAMPLED_LUMA_SHA256 = 'a22d8e31eda8d5f564a44f9c27a48fca80d7b6c05be274ebaf5360da83f83910'
# The pixels of JPGExtended.dcm, a sample file of pydicom.
SAMPLE_FILE_SHA256 = 'd30242775a414c01d616447854ebe3f2b20259822894bcd6891f879bcdcbf313'


def sha256(array):
    return hashlib.sha256(array.astype('<u2').tobytes()).hexdigest()


def make_jpeg(mode='L', **kwargs):
    """An 8-bit JPEG file made by Pillow, with what it decodes to."""
    import numpy

    generator = numpy.random.default_rng(seed=3)
    size = (37, 53) if mode == 'L' else (37, 53, 3)
    image = Image.fromarray(generator.integers(0, 256, size, dtype='uint8'))
    buffer = io.BytesIO()
    image.save(buffer, 'JPEG', quality=90, **kwargs)
    return buffer.getvalue()


class DecoderTestCase(SimpleTestCase):
    def test_12_bits(self):
        samples, precision = jpeg_extended.decode_jpeg(data=JPEG_12_BITS)
        self.assertEqual(precision, 12)
        self.assertEqual(samples.shape, (16, 24, 1))
        self.assertEqual(sha256(samples[:, :, 0]), JPEG_12_BITS_SHA256)

    def test_12_bits_whole_range(self):
        samples, precision = jpeg_extended.decode_jpeg(data=JPEG_12_BITS)
        self.assertEqual((samples.min(), samples.max()), (0, 4095))

    def test_12_bits_color(self):
        samples, precision = jpeg_extended.decode_jpeg(data=JPEG_12_BITS_COLOR)
        self.assertEqual(samples.shape, (16, 24, 3))
        self.assertEqual(sha256(samples), JPEG_12_BITS_COLOR_SHA256)

    def test_12_bits_subsampled(self):
        samples, precision = jpeg_extended.decode_jpeg(
            data=JPEG_12_BITS_SUBSAMPLED
        )
        self.assertEqual(samples.shape, (16, 24, 3))
        self.assertEqual(
            sha256(samples[:, :, 0]), JPEG_12_BITS_SUBSAMPLED_LUMA_SHA256
        )

    def test_8_bits_as_pillow(self):
        for kwargs in (
            {}, {'restart_marker_blocks': 1}, {'restart_marker_blocks': 7},
            {'restart_marker_rows': 1}
        ):
            with self.subTest(kwargs=kwargs):
                data = make_jpeg(**kwargs)
                samples, precision = jpeg_extended.decode_jpeg(data=data)
                self.assertEqual(precision, 8)
                self.assertEqual(
                    samples[:, :, 0].astype('uint8').tobytes(),
                    Image.open(io.BytesIO(data)).tobytes()
                )

    def test_truncated_file_gives_what_it_holds(self):
        import numpy

        generator = numpy.random.default_rng(seed=5)
        buffer = io.BytesIO()
        Image.fromarray(
            generator.integers(0, 256, (256, 256), dtype='uint8')
        ).save(buffer, 'JPEG', quality=90)
        data = buffer.getvalue()
        complete, precision = jpeg_extended.decode_jpeg(data=data)
        with self.assertLogs(jpeg_extended.logger, level='WARNING'):
            partial, precision = jpeg_extended.decode_jpeg(
                data=data[:len(data) * 3 // 4]
            )
        self.assertEqual(partial.shape, complete.shape)
        self.assertEqual(partial[:32].tobytes(), complete[:32].tobytes())
        self.assertEqual(int(partial[-1, -1, 0]), 128)

    def test_files_refused(self):
        progressive = make_jpeg(progressive=True)
        no_frame = JPEG_12_BITS[:JPEG_12_BITS.index(b'\xff\xc1')] + b'\xff\xd9'
        for name, data in {
            'not a JPEG file': b'not a JPEG file',
            'empty': b'',
            'start of image alone': b'\xff\xd8',
            'no frame': no_frame,
            'progressive': progressive,
            'no scan': JPEG_12_BITS[:JPEG_12_BITS.index(b'\xff\xda')],
            'scan without component': JPEG_12_BITS[
                :JPEG_12_BITS.index(b'\xff\xda')
            ] + b'\xff\xda\x00\x03\x00'
        }.items():
            with self.subTest(name=name):
                with self.assertRaises(jpeg_extended.JPEGDecodeError):
                    jpeg_extended.decode_jpeg(data=data)

    def test_declared_size_limits(self):
        position = JPEG_12_BITS.index(b'\xff\xc1') + 5
        for size, message in ((4000, 'too short'), (9000, 'larger than')):
            data = (
                JPEG_12_BITS[:position] + size.to_bytes(2, 'big') * 2 +
                JPEG_12_BITS[position + 4:]
            )
            with self.subTest(size=size):
                with self.assertRaisesMessage(
                    jpeg_extended.JPEGDecodeError, message
                ):
                    jpeg_extended.decode_jpeg(data=data)

    def test_time_limit(self):
        with mock.patch.object(jpeg_extended, 'TIME_MAXIMUM', -1):
            with self.assertRaisesMessage(
                jpeg_extended.JPEGDecodeError, 'not decoded'
            ):
                jpeg_extended.decode_jpeg(data=JPEG_12_BITS)


def make_dicom(
    frames=(JPEG_12_BITS,), photometric='MONOCHROME2', rows=16, columns=24,
    samples=1, signed=0, bits=12, transfer_syntax=None
):
    from pydicom.dataset import Dataset, FileMetaDataset
    from pydicom.encaps import encapsulate
    from pydicom.uid import (
        JPEGExtended12Bit, SecondaryCaptureImageStorage, generate_uid
    )

    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = transfer_syntax or JPEGExtended12Bit
    dataset = Dataset()
    dataset.file_meta = meta
    dataset.SOPClassUID = SecondaryCaptureImageStorage
    dataset.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    dataset.Modality = 'OT'
    dataset.Rows, dataset.Columns = rows, columns
    dataset.SamplesPerPixel = samples
    if samples > 1:
        dataset.PlanarConfiguration = 0
    dataset.PhotometricInterpretation = photometric
    dataset.BitsAllocated = 16 if bits > 8 else 8
    dataset.BitsStored, dataset.HighBit = bits, bits - 1
    dataset.PixelRepresentation = signed
    dataset.NumberOfFrames = len(frames)
    dataset.PixelData = encapsulate(list(frames))
    dataset['PixelData'].is_undefined_length = True
    dataset['PixelData'].VR = 'OB'
    buffer = io.BytesIO()
    dataset.save_as(buffer, enforce_file_format=True)
    buffer.seek(0)
    return buffer


@unittest.skipUnless(PYDICOM, 'pydicom not installed')
class DICOMTestCase(SimpleTestCase):
    def test_sample_file_of_pydicom(self):
        from pydicom.data import get_testdata_file
        from pydicom.pixels import pixel_array

        path = get_testdata_file('JPGExtended.dcm', download=False)
        if not path:
            self.skipTest('sample file of pydicom not installed')

        array = pixel_array(
            path, decoding_plugin=jpeg_extended.register_decoder()
        )
        self.assertEqual(sha256(array), SAMPLE_FILE_SHA256)

        with open(path, mode='rb') as file_object:
            self.assertEqual(
                dicom.get_dicom_page_count(file_object=file_object), 1
            )
            image = dicom.render_dicom_page(
                file_object=file_object, page_number=0
            )
        # The image itself, not a page of attributes with the reason.
        self.assertEqual(image.size, (256, 1024))

    def test_no_decoder_refusal_logged(self):
        # Pillow is not asked for the samples of 12 bits.
        with self.assertNoLogs('pydicom', level='ERROR'):
            dicom.render_dicom_page(file_object=make_dicom(), page_number=0)

    def test_values(self):
        from pydicom.pixels import pixel_array

        array = pixel_array(
            make_dicom(), decoding_plugin=jpeg_extended.register_decoder(),
            index=0
        )
        self.assertEqual(sha256(array), JPEG_12_BITS_SHA256)

    def test_each_frame_on_its_page(self):
        from pydicom.pixels import pixel_array

        file_object = make_dicom(frames=(JPEG_12_BITS, JPEG_12_BITS_INVERTED))
        self.assertEqual(dicom.get_dicom_page_count(file_object=file_object), 2)
        first = dicom.render_dicom_page(file_object=file_object, page_number=0)
        second = dicom.render_dicom_page(file_object=file_object, page_number=1)
        self.assertEqual(first.size, (528, 352))
        self.assertEqual(second.size, (528, 352))
        self.assertLess(first.getpixel((0, 0)), second.getpixel((0, 0)))

        for index, expected in enumerate(
            (JPEG_12_BITS_SHA256, JPEG_12_BITS_INVERTED_SHA256)
        ):
            file_object.seek(0)
            self.assertEqual(
                sha256(
                    pixel_array(
                        file_object, index=index,
                        decoding_plugin=jpeg_extended.register_decoder()
                    )
                ), expected
            )

    def test_8_bits_samples(self):
        from pydicom.pixels import pixel_array

        data = make_jpeg()
        array = pixel_array(
            make_dicom(
                bits=8, columns=53, frames=(data,), rows=37
            ), decoding_plugin=jpeg_extended.register_decoder(), index=0
        )
        self.assertEqual(array.dtype, 'uint8')
        self.assertEqual(array.tobytes(), Image.open(io.BytesIO(data)).tobytes())

    def test_signed_samples(self):
        from pydicom.pixels import pixel_array

        array = pixel_array(
            make_dicom(signed=1),
            decoding_plugin=jpeg_extended.register_decoder(), index=0
        )
        self.assertEqual((array.min(), array.max()), (-2048, 2047))

    def test_color_values(self):
        from pydicom.pixels import pixel_array

        array = pixel_array(
            make_dicom(
                frames=(JPEG_12_BITS_COLOR,), photometric='YBR_FULL', samples=3
            ), decoding_plugin=jpeg_extended.register_decoder(), index=0
        )
        self.assertEqual(sha256(array), JPEG_12_BITS_COLOR_RGB_SHA256)

    def test_color_samples_kept_when_not_ybr(self):
        from pydicom.pixels import pixel_array

        # Without its JFIF marker: pydicom reads the file as YCbCr with it.
        size = int.from_bytes(JPEG_12_BITS_COLOR[4:6], 'big')
        data = JPEG_12_BITS_COLOR[:2] + JPEG_12_BITS_COLOR[4 + size:]
        array = pixel_array(
            make_dicom(frames=(data,), photometric='RGB', samples=3),
            decoding_plugin=jpeg_extended.register_decoder(), index=0
        )
        self.assertEqual(sha256(array), JPEG_12_BITS_COLOR_SHA256)

    def test_color_pages(self):
        for photometric, data in (
            ('YBR_FULL', JPEG_12_BITS_COLOR),
            ('YBR_FULL_422', JPEG_12_BITS_SUBSAMPLED)
        ):
            with self.subTest(photometric=photometric):
                image = dicom.render_dicom_page(
                    file_object=make_dicom(
                        frames=(data,), photometric=photometric, samples=3
                    ), page_number=0
                )
                # The image itself, not a page of attributes with the reason:
                # the ramp goes from blue to red, the third channel inverted.
                self.assertEqual(image.size, (528, 352))
                red, green, blue = image.getpixel((0, 0))
                self.assertLess(red, 30)
                self.assertGreater(blue, 225)
                red, green, blue = image.getpixel((527, 351))
                self.assertGreater(red, 225)
                self.assertLess(blue, 30)

    def test_size_other_than_the_declared_one(self):
        image = dicom.render_dicom_page(
            file_object=make_dicom(rows=20), page_number=0
        )
        # A page of attributes with the reason.
        self.assertEqual(image.size, (dicom.PAGE_WIDTH, dicom.PAGE_HEIGHT))

    def test_damaged_frame_gives_a_page_with_the_reason(self):
        image = dicom.render_dicom_page(
            file_object=make_dicom(frames=(b'not a JPEG file!',)), page_number=0
        )
        self.assertEqual(image.size, (dicom.PAGE_WIDTH, dicom.PAGE_HEIGHT))
