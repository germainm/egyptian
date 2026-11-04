"""
Decoder of the lossless JPEG images. The images of the fixtures come from
libjpeg-turbo 3.1.3, which this project does not depend on; the others from the
encoder below, for what libjpeg-turbo does not write from Python: their files
were checked once against libjpeg-turbo. Being lossless, each image must give
exactly the samples it was made from.
"""
import base64
import contextlib
import hashlib
import importlib.util
import time
import unittest
from unittest import mock

from django.test import SimpleTestCase

from ..renderers import dicom, jpeg_lossless
from .test_jpeg_extended import JPEG_12_BITS, make_dicom, make_jpeg

PYDICOM = importlib.util.find_spec('pydicom') is not None

JPEG_PREDICTOR_1 = base64.b64decode((
    '/9j/4AAQSkZJRgABAQAAAQABAAD/wwALDAAMABABAREA/8QAGQABAQEBAQEAAAAAAAAAAA'
    'AACQgHDAoL/9oACAEBAAEAAOf/ANc17YNi2TZto2rbNu3Dct03beEl3zfqAoKhKGoiiqMo'
    '6kKSpSlqY9ktOU9UFRVJU1UVVVlXVhWVaVtXH1Ja8r6wLCsSxrIsrgy7OtC0rUta2Ockty'
    '3rguK5Lmui6rsu68LyvS9r46SW/L+QBAkEQbhB0KQxDkQRJFEWRj5kiOI8kCRJIkyUJUln'
    'CWpgmSaJsnHkkTxPlAUJRFGUhSlMU7hT1SVRVlYiRXFeWBYlkWZaFqWxbuFvXJdF2XhJV8'
    'X5gGCYRhmIYpjOGNZBkmUZZmPZKzjPNA0TSNNw07VNY1zYNk2jbNx9SVvG+cDhwXEcZyHK'
    'cxznQdLh03Wdj//Z'
))
JPEG_PREDICTOR_2 = base64.b64decode((
    '/9j/4AAQSkZJRgABAQAAAQABAAD/wwALDAAMABABAREA/8QAHAAAAwEBAQEBAQAAAAAAAA'
    'AACgsMCQcIBgMF/9oACAEBAAIAAJ//AK517sHYuydm7R2rtnbu4dy7p3bvGkuousuwu0u4'
    'u8pApEpIpMpQpUpYpcpgpkpopspwp0p4p8rAVhKxFYyshWUrMVnK0FaStRWsrYVtK3Fbyu'
    'BXEsyJMyTQk1JNiTck4JOSTok7JPCT0k+JPyIBEElCLQy0QtFLRi0ctILSS0otLLTC00tO'
    'LTyqBFEikRTIqEVSKxFciwRZItEWyLhF0i8RfJYC2EtiKDIEIFIGIHIIIJIKILIMINIOIP'
    'JgJhJiJcy5CZSZiZyeBPEnkTzJwTknwn8T9fpei9l9C+pfYvuXQXSXUXWXYXaXcXeUgUiU'
    'kWJkKFKlLFLlMFMlNFNlOFOlPFPlkBJCSREYyshWUrMVnK0FaStRWsrYWWklxJeRwK4lci'
    'uZXQrqWbEm5JwT/9k='
))
JPEG_PREDICTOR_3 = base64.b64decode((
    '/9j/4AAQSkZJRgABAQAAAQABAAD/wwALDAAMABABAREA/8QAHAAAAwEBAQEBAQAAAAAAAA'
    'AACgsMCQcIBgMF/9oACAEBAAMAAJ//AK517sHYuydm7R2rtnbu4dy7p3bvGku0O4e8pA5F'
    'JJZNpR5WJaZepi5nJrZvpkp4J8bAVhOxJY1sjWV7NFnm0VabtWWvbZ1pK3hcBuJXI7ml0W'
    '6tdnzeE4lOaTq07xPNT3k5IgAQRIREMyIhFUjMR3JEKTOlVpd6Zmm7p3aSWohqQ6mWqHqq'
    'astXYsOWYLUlui5ZdwvaX+LJAQAYghApgyA6hDLS+1RFyGUG2HYH6wcEkxgyCykzGzo8Fe'
    'LPJ3nDiXNPlvw/t/e+JPQPqP2L7n0J0r1N1v2R2zh1N9yGSOyXdJSoSwy5TBzKTSzbTjzs'
    'Y9KP0YLsOWLbH0yVmCzjaCtJ2pLWuWMlrpdCXycKuN3LLnt060ldwvA3ks6NO0TxU9Y/Pf'
    '40CdBrQroeETSLz//Z'
))
JPEG_PREDICTOR_4 = base64.b64decode((
    '/9j/4AAQSkZJRgABAQAAAQABAAD/wwALDAAMABABAREA/8QAGwABAAIDAQEAAAAAAAAAAA'
    'AABgcMCgsNCQj/2gAIAQEABAAAr/8ALkvTBMUyTNNE1TZN04TlOk7Tx6SoECBAgQIECBAg'
    'QIECDMlQIECBAgQIECBAgQIEG0lQIECBAgQIKA+gQIECBBXJECBAgQIECDoECBAgQIEFkl'
    'QIECBAgoD6BAgQIECBBrJECBAgQIOgQIEFAfQIECBBiSIECBAgQIECDoEFAfQIECD4kQIE'
    'CBAgQIECBAgQIEHpKgQIECBAgQIKA/0CBAgQIMyVAgQIECCgPoEHQIECBAgQbSVAgQUB9A'
    'g6BAgQIECCgPoEH//Z'
))
JPEG_PREDICTOR_5 = base64.b64decode((
    '/9j/4AAQSkZJRgABAQAAAQABAAD/wwALDAAMABABAREA/8QAGQABAQEBAQEAAAAAAAAAAA'
    'AACAcMCwoJ/9oACAEBAAUAAM//AFyvWCxWSzWi1Wy3XC5XS7Xj6S06n1Co1Kp1Sq1ar1is'
    '1qt1z2S16v2Cw2Kx2Sy2az2i02q12zqS2633C43K53S64HW73i83q93zOSX6/oBAoJBoRC'
    '6IZDohEopFozSSo5HpBIpJJ4JNKpZLphMppNpzmSJ5PqBQqJR6KRSqbBTKhUqpVqzySK5X'
    'rBYrJZrRarbRb4LdcrpdrwSL5fsBgsJhsRisZj8Mdksplsz6Ss5ntBotJptRqtbBraNhst'
    'pttz2St5vuBwuJx4ONyubRzuh0up1uzqSu53vDB4PJ56PR6vZ7vh84Pl9vz//Z'
))
JPEG_PREDICTOR_6 = base64.b64decode((
    '/9j/4AAQSkZJRgABAQAAAQABAAD/wwALDAAMABABAREA/8QAHQAAAgMBAQEBAQAAAAAAAA'
    'AACQoHCAsMBgUCBP/aAAgBAQAGAADn/wCXJemCYpkmaaJqmybpwnKdJ2ngkts7h3TvHfMg'
    'ZEyRkzKGVMsZczBmTclNmcM6Z4z5sBsJsRsZshspsxs5tBtJ6krWbYbabcbebgbibkfGZZ'
    'oWalmxZuWcFnJc5JnZZ4WelnxZ+SASCSEXYZ6Ieinox6OekHpJ9JLpZ6Yemnpx6eeoHyiS'
    'kSmSoSqSsSuSwSyWZItkuEukvEvkALuE9iPYz5kIKQYg5CCEkpILIYQ0hxDyoFRKkVMu9D'
    '51KsVcoChKkkZeC8l8L+L9/T9H7OQ5TmOc7B2TJLbO4d07x3zIGRMkZM+FC6VMsZczBmTc'
    'lNmcM6Z4z5sB8QlkRZGXUhspsxs5tBtJ6krWbYbafFxZeWYF1ibkbmbobqbsfG5ZwWcl/9'
    'k='
))
JPEG_PREDICTOR_7 = base64.b64decode((
    '/9j/4AAQSkZJRgABAQAAAQABAAD/wwALDAAMABABAREA/8QAHQAAAwEBAQADAQAAAAAAAA'
    'AACQoLBwgMAwQGBf/aAAgBAQAHAADz/wDrmvbBsWybNtG1bZt24blum7bwSXuHvIgZFCSk'
    '2KOVgtJejFmcNab457kp8WAmE2JGNWRmV2aGeWimm2rGvWzm36krgLiTkbmjorqzs7vHji'
    'JzM6qd3PMnuz7vOSIIIQoZIhoqIyo7JD0maVVLumZTdp3U/wD0ktSGplVDqqVZau3lhll1'
    'qFuVyl217F/QHTJAYBBCkGMOghbS9qi1z5skbQ6x+cG8PKScgco8xc54JiuTZv8AiL7Xn6'
    'vj+7/e/X8SajsW59CdK9Tdb9kds91Q+iGEdJcT8kpYS5GDMoaU2xxzsHp8PywWw4xax8ye'
    '5Kzi0E0m1I1q2N4taXPL4cKcbcsc9dOdfqSvAvJPR+OzniT1X53+KBNBqhXQ88iYi6jd/9'
    'k='
))
# 16 bits, with a difference of 32768: the size that has no additional bits.
JPEG_16_BITS = base64.b64decode((
    '/9j/4AAQSkZJRgABAQAAAQABAAD/wwALEAAMABABAREA/8QAHAABAQEAAgMBAAAAAAAAAA'
    'AACQgHDA0KCxAP/9oACAEBAAEAAPvvwC52DYtk2baNq2zbtw3LdN23hJd836gKCoShqIoq'
    'jKOpCkqUpamPMlpynqgqKpKmqiqqsq6sKyrStq49pLXlfWBYViWNZFlWZZ1oWlalrWx7yW'
    '3LeuC4rkua6Lquy7rwvK9L2vjkkt+X8gCBIIgyEIUhiHIgiSKIsjHLJUcR5IEiSRJkoSpL'
    'EuTBMk0TZOOaSp4nygKEoijKQpSmKcqCpKoqysc8lVxXlgWJZFmWhalsW5cFyXRdl47ElX'
    'xfmAYJhGGYhimMY5kGSZRlmY7MlZxnmgaJpGmahqmsa5sGybRtm47UlbxvnAcJxHGchynM'
    'c50HSdR1nY//2Q=='
))
# Three components of 8 bits, in RGB.
JPEG_COLOR = base64.b64decode((
    '/9j/7gAOQWRvYmUAZAAAAAAA/8MAEQgADAAQA1IRAEcRAEIRAP/EABsAAAMBAQEBAQAAAA'
    'AAAAAAAAYHCAUEAwIA/9oADANSAEcAQgABAACf9d/txdqNvL1Qy/YFQOIBTrkA03MoLTTo'
    'shLzSE0s7AtJu4NSM3h9IPK0kbOYnRj2FUTO4vRBKNDT8TaDn2nqCoBPz+gaif1CKOe0Kp'
    'X1RFUTuiVS9qMVc5o2rnlSCvm9IrF3JOtHZSy1mlLrd0Eo0NU4/JjTs+uJP0A4KiQMuqOh'
    'G4pUK2qooiV1SiWsq6MalXI2UVej2gsaSZ1aJOS1rSzKW6XZBKNDS7bjEr5vSCv5fYAC4j'
    '4DmM8sZzRyDug4CZpNgt2GgbNplaDwi8ReRcJzmWCr2KhedyglGhobPCQdPiIfYBBgsLeu'
    'SQ4bxWNtY7I2MmSdbLZmpms7Sz5P0OFpd3G1OzllXq52x0EttjXnuenzDv1+IP30RfPoSe'
    'fsTePQUc/UVcvZFfH3F3DoGGfCJld2oaZetGuTsHGOSjQ1ueeHDvzcRB+HyL6HST0Gyb2G'
    'SjoFyrqFYr7LULu4RMNAPMoRDTTUC411rKONgHiQats8GwM+HQFgD6/YWCvZDuSvGNirlk'
    'Y63knJrZmZazZ2asZPz6waXCrWpxquVeWqmxzqclGhpuLtRt6vlDL6/qBxAKdmMDpxzWMm'
    'XQDpeaQmlnYFpObQ2knhaCPeQijZzE6MewqiZ3F6IJRoaflOIOfU7QVAJ+f0DUT+oRRz2h'
    'VK+qIqid0SqXtRirnNG1c8ker3hSSxm1J1o7KWWs0pdbuglGhpNvxyU9Pswp+gHBUSBl1R'
    '0I3FKhW1VFESuqUS1lXRjUq5Gyir6QaCxSLOrRJyWtaWZS3S7IJRoaXbcYi9bzCsCX4/AX'
    'EfAbkPAWZTqyHRG4TNJsFuw0DXcZB83mFpPKLROcywVexULzuUf//Z'
))
# The pixels of SC_rgb_jpeg_gdcm.dcm, a sample file of pydicom, read by GDCM.
SAMPLE_FILE_SHA256 = '169e619557b12114a7f0be8602026e9abb3d5045804311736ec14cecb026aca9'


def make_source(precision=12, rows=12, columns=16):
    import numpy

    values = numpy.add.outer(
        numpy.arange(rows) * 37, numpy.arange(columns) * 91
    ) + numpy.arange(rows * columns).reshape(rows, columns) ** 2
    return (values % (1 << precision)).astype('uint16')


def make_lossless_jpeg(
    source, predictor=1, precision=12, transform=0, restart_rows=0
):
    """
    A lossless JPEG file of one component, for what libjpeg-turbo does not
    write from Python: restart intervals and point transforms.
    """
    rows, columns = source.shape
    categories = list(range(17))
    table_lengths = [0] * 16
    # Five bits for each category: no code of only ones.
    table_lengths[4] = 17
    codes = {category: (index, 5) for index, category in enumerate(categories)}

    def segment(marker, content):
        return b'\xff' + bytes((marker,)) + (len(content) + 2).to_bytes(2, 'big') + content

    output = bytearray(b'\xff\xd8')
    output += segment(
        0xC3, bytes((precision,)) + rows.to_bytes(2, 'big') +
        columns.to_bytes(2, 'big') + b'\x01\x01\x11\x00'
    )
    output += segment(0xC4, b'\x00' + bytes(table_lengths) + bytes(categories))
    if restart_rows:
        output += segment(0xDD, (restart_rows * columns).to_bytes(2, 'big'))
    output += segment(
        0xDA, b'\x01\x01\x00' + bytes((predictor, 0, transform))
    )

    values = [[int(item) >> transform for item in row] for row in source]
    initial = 1 << (precision - transform - 1)
    accumulator = 0
    bits = 0
    scan = bytearray()

    def write(value, size):
        nonlocal accumulator, bits
        accumulator = (accumulator << size) | value
        bits += size
        while bits >= 8:
            byte = (accumulator >> (bits - 8)) & 255
            scan.append(byte)
            if byte == 255:
                scan.append(0)
            bits -= 8
        accumulator &= (1 << bits) - 1

    def flush():
        nonlocal accumulator, bits
        if bits:
            write((1 << (8 - bits)) - 1, 8 - bits)

    interval = 0
    for row in range(rows):
        first_row = row == 0
        if restart_rows and row and not row % restart_rows:
            flush()
            scan += b'\xff' + bytes((0xD0 + interval % 8,))
            interval += 1
            first_row = True

        for column in range(columns):
            if first_row:
                prediction = values[row][column - 1] if column else initial
            elif not column:
                prediction = values[row - 1][0]
            else:
                a = values[row][column - 1]
                b = values[row - 1][column]
                c = values[row - 1][column - 1]
                prediction = (
                    None, a, b, c, a + b - c, a + ((b - c) >> 1),
                    b + ((a - c) >> 1), (a + b) >> 1
                )[predictor]

            difference = (values[row][column] - prediction) & 65535
            if difference >= 32768 and difference != 32768:
                difference -= 65536
            size = 16 if difference == 32768 else abs(difference).bit_length()
            write(*codes[size])
            if size and size < 16:
                write(
                    difference if difference > 0 else difference + (1 << size) - 1,
                    size
                )
    flush()
    return bytes(output + scan + b'\xff\xd9')


def decode(data):
    return jpeg_lossless.decode_jpeg_lossless(data=data)


class DecoderTestCase(SimpleTestCase):
    def test_each_predictor(self):
        for predictor, data in enumerate(
            (
                JPEG_PREDICTOR_1, JPEG_PREDICTOR_2, JPEG_PREDICTOR_3,
                JPEG_PREDICTOR_4, JPEG_PREDICTOR_5, JPEG_PREDICTOR_6,
                JPEG_PREDICTOR_7
            ), start=1
        ):
            with self.subTest(predictor=predictor):
                samples, precision = decode(data=data)
                self.assertEqual(precision, 12)
                self.assertEqual(samples.shape, (12, 16, 1))
                self.assertEqual(
                    samples[:, :, 0].tolist(), make_source().tolist()
                )

    def test_16_bits_and_largest_difference(self):
        source = make_source(precision=16)
        source[0, 1] = (int(source[0, 0]) + 32768) % 65536
        samples, precision = decode(data=JPEG_16_BITS)
        self.assertEqual(precision, 16)
        self.assertEqual(samples[:, :, 0].tolist(), source.tolist())

    def test_color(self):
        import numpy

        source = make_source(precision=8)
        expected = numpy.stack((source, source[::-1], 255 - source), axis=2)
        samples, precision = decode(data=JPEG_COLOR)
        self.assertEqual(precision, 8)
        self.assertEqual(samples.tolist(), expected.tolist())

    def test_restart_intervals(self):
        source = make_source()
        for predictor in range(1, 8):
            for restart_rows in (1, 2, 5):
                with self.subTest(predictor=predictor, restart_rows=restart_rows):
                    samples, precision = decode(
                        data=make_lossless_jpeg(
                            source=source, predictor=predictor,
                            restart_rows=restart_rows
                        )
                    )
                    self.assertEqual(samples[:, :, 0].tolist(), source.tolist())

    def test_point_transform(self):
        source = (make_source() >> 2) << 2
        for predictor in range(1, 8):
            with self.subTest(predictor=predictor):
                samples, precision = decode(
                    data=make_lossless_jpeg(
                        source=source, predictor=predictor, transform=2
                    )
                )
                self.assertEqual(samples[:, :, 0].tolist(), source.tolist())

    def test_small_sizes(self):
        for rows, columns in ((1, 1), (1, 9), (9, 1)):
            for predictor in (1, 6, 7):
                with self.subTest(rows=rows, columns=columns, predictor=predictor):
                    source = make_source(rows=rows, columns=columns)
                    samples, precision = decode(
                        data=make_lossless_jpeg(
                            source=source, predictor=predictor
                        )
                    )
                    self.assertEqual(samples[:, :, 0].tolist(), source.tolist())

    def test_truncated_file_gives_what_it_holds(self):
        source = make_source(rows=64, columns=64)
        data = make_lossless_jpeg(source=source)
        with self.assertLogs(jpeg_lossless.logger, level='WARNING'):
            samples, precision = decode(data=data[:len(data) * 3 // 4])
        self.assertEqual(samples.shape, (64, 64, 1))
        self.assertEqual(samples[:32, :, 0].tolist(), source[:32].tolist())

    def test_invalid_code(self):
        source = make_source(rows=64, columns=64)
        data = bytearray(make_lossless_jpeg(source=source))
        # Five bits of ones: the encoder gives no such code.
        data[len(data) // 2:len(data) // 2 + 6] = b'\xff\x00\xff\x00\xff\x00'
        with self.assertLogs(jpeg_lossless.logger, level='WARNING'):
            samples, precision = decode(data=bytes(data))
        self.assertEqual(samples[:16, :, 0].tolist(), source[:16].tolist())

    def test_files_refused(self):
        lossless = make_lossless_jpeg(source=make_source())
        scan = lossless.index(b'\xff\xda')
        predictor_position = scan + 7
        for name, data, message in (
            ('not a JPEG file', b'not a JPEG file', 'start of image'),
            ('empty', b'', 'start of image'),
            ('start of image alone', b'\xff\xd8', 'no frame header'),
            ('sequential', JPEG_12_BITS, 'sequential'),
            ('progressive', make_jpeg(progressive=True), 'progressive'),
            ('no scan', lossless[:scan], 'no image data'),
            (
                'predictor 0', lossless[:predictor_position] + b'\x00' +
                lossless[predictor_position + 1:], 'predictor 0'
            ),
            (
                'predictor 8', lossless[:predictor_position] + b'\x08' +
                lossless[predictor_position + 1:], 'predictor 8'
            )
        ):
            with self.subTest(name=name):
                with self.assertRaisesMessage(
                    jpeg_lossless.JPEGDecodeError, message
                ):
                    decode(data=data)

    def test_restart_interval_of_part_of_a_row(self):
        data = make_lossless_jpeg(source=make_source(), restart_rows=1)
        # 16 samples in a row: an interval of 15.
        position = data.index(b'\xff\xdd') + 4
        data = data[:position] + (15).to_bytes(2, 'big') + data[position + 2:]
        with self.assertRaisesMessage(
            jpeg_lossless.JPEGDecodeError, 'number of rows'
        ):
            decode(data=data)

    def test_subsampled_color_refused(self):
        position = JPEG_COLOR.index(b'\xff\xc3')
        data = bytearray(JPEG_COLOR)
        # Sampling factors of the first component.
        data[position + 11] = 0x22
        with self.assertRaisesMessage(
            jpeg_lossless.JPEGDecodeError, 'subsampled'
        ):
            decode(data=bytes(data))

    def test_declared_size_limits(self):
        data = make_lossless_jpeg(source=make_source())
        position = data.index(b'\xff\xc3') + 5
        for size, message in ((4000, 'too short'), (9000, 'larger than')):
            with self.subTest(size=size):
                with self.assertRaisesMessage(
                    jpeg_lossless.JPEGDecodeError, message
                ):
                    decode(
                        data=data[:position] + size.to_bytes(2, 'big') * 2 +
                        data[position + 4:]
                    )

    def test_time_limit(self):
        with mock.patch.object(jpeg_lossless, 'TIME_MAXIMUM', -1):
            with self.assertRaisesMessage(
                jpeg_lossless.JPEGDecodeError, 'not decoded'
            ):
                decode(data=make_lossless_jpeg(source=make_source()))


@unittest.skipUnless(PYDICOM, 'pydicom not installed')
@contextlib.contextmanager
def readers_results():
    """The results of the arrays of readers, each one for a segment."""
    original = jpeg_lossless._read_segment_with_readers
    results = []

    def wrapper(**kwargs):
        results.append(original(**kwargs))
        return results[-1]

    with mock.patch.object(jpeg_lossless, '_read_segment_with_readers', wrapper):
        yield results


class ReadersTestCase(SimpleTestCase):
    """
    The arrays of readers against the Python loop, which defines the behavior.
    """
    def setUp(self):
        import numpy

        # Differences of many sizes, as in a real image: codes of many lengths.
        random = numpy.random.default_rng(5)
        self.source = (
            random.normal(2000, 12, (128, 128)).astype(numpy.int64) +
            numpy.arange(128) * 3
        ).astype(numpy.uint16)

    def assert_same(self, first, second):
        # Not assertEqual: on lists this long, its message takes minutes.
        import numpy

        self.assertTrue(numpy.array_equal(first, second), 'Different samples.')

    def decode_both(self, data):
        with mock.patch.object(
            jpeg_lossless, 'READERS_SAMPLES_MINIMUM', new=1 << 40
        ):
            expected = decode(data=data)
        with readers_results() as results:
            samples, precision = decode(data=data)
        self.assert_same(samples, expected[0])
        self.assertEqual(precision, expected[1])
        return samples, results

    def test_each_predictor(self):
        for predictor in range(1, 8):
            with self.subTest(predictor=predictor):
                samples, results = self.decode_both(
                    data=make_lossless_jpeg(
                        predictor=predictor, source=self.source
                    )
                )
                self.assertEqual(results, [True])
                self.assert_same(samples[:, :, 0], self.source)

    def test_diagonals_of_every_shape(self):
        import numpy

        random = numpy.random.default_rng(7)
        for rows, columns in (
            (1, 1), (1, 7), (7, 1), (2, 2), (2, 9), (9, 2), (3, 3), (5, 40),
            (40, 5)
        ):
            source = random.integers(0, 4096, (rows, columns)).astype(
                numpy.uint16
            )
            for predictor in (6, 7):
                with self.subTest(
                    rows=rows, columns=columns, predictor=predictor
                ):
                    samples, precision = decode(
                        data=make_lossless_jpeg(
                            predictor=predictor, source=source
                        )
                    )
                    self.assert_same(samples[:, :, 0], source)

    def test_long_differences_and_largest_one(self):
        import numpy

        # Codes of five bits with up to 15 additional bits do not fit in the 16
        # bits of the tables, and a difference of 32768 has no additional bits.
        random = numpy.random.default_rng(6)
        source = random.normal(30000, 4000, (128, 128)).clip(0, 65535).astype(
            numpy.uint16
        )
        source[:64] = (self.source[:64] % 512) + 200
        source[::8, ::2] = 40000
        source[::8, 1::2] = 7232
        samples, results = self.decode_both(
            data=make_lossless_jpeg(precision=16, source=source)
        )
        self.assertEqual(results, [True])
        self.assert_same(samples[:, :, 0], source)

    def test_fixtures_of_libjpeg_turbo(self):
        # Too small for the readers to succeed each time: the result must not
        # depend on it.
        with mock.patch.multiple(
            jpeg_lossless, READERS_SAMPLES_MINIMUM=1,
            READERS_SPACING_MINIMUM=256, READERS_SYNCHRONIZATION=16
        ):
            for predictor, data in enumerate(
                (
                    JPEG_PREDICTOR_1, JPEG_PREDICTOR_2, JPEG_PREDICTOR_3,
                    JPEG_PREDICTOR_4, JPEG_PREDICTOR_5, JPEG_PREDICTOR_6,
                    JPEG_PREDICTOR_7
                ), start=1
            ):
                with self.subTest(predictor=predictor):
                    samples, precision = decode(data=data)
                    self.assert_same(samples[:, :, 0], make_source())

    def test_restart_intervals_and_transform(self):
        import numpy

        source = numpy.tile(self.source, (2, 1))
        source = (source >> 2) << 2
        for predictor in (1, 4, 6, 7):
            with self.subTest(predictor=predictor):
                samples, results = self.decode_both(
                    data=make_lossless_jpeg(
                        predictor=predictor, source=source, restart_rows=128,
                        transform=2
                    )
                )
                self.assertEqual(results, [True, True])
                self.assert_same(samples[:, :, 0], source)

    def test_stream_that_does_not_resynchronize(self):
        import numpy

        # Codes of five bits only: a reader that starts inside one stays there.
        source = numpy.full((128, 128), 1000, dtype=numpy.uint16)
        samples, results = self.decode_both(
            data=make_lossless_jpeg(source=source)
        )
        self.assertEqual(results, [False])
        self.assert_same(samples[:, :, 0], source)

    def test_truncated_streams(self):
        data = make_lossless_jpeg(source=self.source)
        start = data.index(b'\xff\xda') + 10
        for share in (25, 50, 90, 99, 100):
            with self.subTest(share=share):
                self.decode_both(
                    data=data[:start + (len(data) - 2 - start) * share // 100]
                )
        # The last code cut in two.
        for missing in range(1, 8):
            with self.subTest(missing=missing):
                self.decode_both(data=data[:-2 - missing])

    def test_invalid_codes(self):
        data = make_lossless_jpeg(source=self.source)
        start = data.index(b'\xff\xda') + 10
        for position in (start + 1, (start + len(data)) // 2, len(data) - 20):
            with self.subTest(position=position):
                damaged = bytearray(data)
                # Five bits of ones: the encoder gives no such code.
                damaged[position:position + 6] = b'\xff\x00\xff\x00\xff\x00'
                samples, results = self.decode_both(data=bytes(damaged))
                self.assertEqual(results, [False])

    def test_invalid_code_with_enough_data_after_it(self):
        # The count of differences does not reveal the damage: more data comes.
        data = make_lossless_jpeg(source=self.source)
        start = data.index(b'\xff\xda') + 10
        scan = bytearray(data[start:-2])
        scan[len(scan) // 2:len(scan) // 2 + 6] = b'\xff\x00\xff\x00\xff\x00'
        samples, results = self.decode_both(
            data=data[:start] + bytes(scan) + data[start:-2] + data[-2:]
        )
        self.assertEqual(results, [False])

    def test_data_after_the_image(self):
        data = make_lossless_jpeg(source=self.source)
        samples, results = self.decode_both(
            data=data[:-2] + bytes(1000) + data[-2:]
        )
        self.assertEqual(results, [True])

    def test_readers_at_the_end_of_the_stream(self):
        # So many readers that some leave the data while they synchronize.
        data = make_lossless_jpeg(source=self.source)
        with mock.patch.multiple(
            jpeg_lossless, READERS_SPACING_MINIMUM=8,
            READERS_SPACING_SHIFT=30, READERS_SYNCHRONIZATION=2000
        ):
            samples, results = self.decode_both(data=data)
        self.assert_same(samples[:, :, 0], self.source)

    def test_reader_that_does_not_resynchronize_in_time(self):
        # Too few differences to resynchronize: a part is taken over by the
        # reader before it, up to one that fell on the right codes.
        data = make_lossless_jpeg(source=self.source)
        with mock.patch.multiple(
            jpeg_lossless, READERS_FAILURES_DIVISOR=1,
            READERS_SYNCHRONIZATION=8
        ):
            samples, results = self.decode_both(data=data)
        self.assertEqual(results, [True])
        self.assert_same(samples[:, :, 0], self.source)

    def test_several_tables_read_by_the_loop(self):
        with readers_results() as results, self.assertRaises(
            jpeg_lossless.JPEGDecodeError
        ):
            jpeg_lossless._read_differences(
                columns=2, count=1 << 16, deadline=time.monotonic() + 9,
                restart_interval=0, segments=(b'',),
                tables=[[0] * 65536, [0] * 65536]
            )
        self.assertEqual(results, [])


class DICOMTestCase(SimpleTestCase):
    def _pixel_array(self, file_object, **kwargs):
        from pydicom.pixels import pixel_array

        jpeg_lossless.register_decoder()
        return pixel_array(
            file_object, decoding_plugin=jpeg_lossless.PLUGIN_LABEL, **kwargs
        )

    def test_both_transfer_syntaxes(self):
        from pydicom.uid import JPEGLossless, JPEGLosslessSV1

        for transfer_syntax, data in (
            (JPEGLossless, JPEG_PREDICTOR_6),
            (JPEGLosslessSV1, JPEG_PREDICTOR_1)
        ):
            with self.subTest(transfer_syntax=transfer_syntax):
                array = self._pixel_array(
                    make_dicom(
                        columns=16, frames=(data,), rows=12,
                        transfer_syntax=transfer_syntax
                    ), index=0
                )
                self.assertEqual(array.tolist(), make_source().tolist())

    def test_each_frame_on_its_page(self):
        from pydicom.uid import JPEGLossless

        file_object = make_dicom(
            columns=16, frames=(JPEG_PREDICTOR_1, JPEG_PREDICTOR_7), rows=12,
            transfer_syntax=JPEGLossless
        )
        self.assertEqual(dicom.get_dicom_page_count(file_object=file_object), 2)
        for page_number in (0, 1):
            image = dicom.render_dicom_page(
                file_object=file_object, page_number=page_number
            )
            # The image itself, enlarged, not a page of attributes.
            self.assertEqual(image.size, (512, 384))

    def test_signed_samples(self):
        from pydicom.uid import JPEGLossless

        array = self._pixel_array(
            make_dicom(
                columns=16, frames=(JPEG_PREDICTOR_1,), rows=12, signed=1,
                transfer_syntax=JPEGLossless
            ), index=0
        )
        source = make_source().astype('int32')
        source[source >= 2048] -= 4096
        self.assertEqual(array.tolist(), source.tolist())

    def test_sample_file_of_pydicom(self):
        from pydicom.data import get_testdata_file

        path = get_testdata_file('SC_rgb_jpeg_gdcm.dcm', download=False)
        if not path:
            self.skipTest('sample file of pydicom not installed')

        array = self._pixel_array(path, raw=True)
        self.assertEqual(
            hashlib.sha256(array.tobytes()).hexdigest(), SAMPLE_FILE_SHA256
        )
        with open(path, mode='rb') as file_object:
            image = dicom.render_dicom_page(
                file_object=file_object, page_number=0
            )
        self.assertEqual(image.size, (600, 600))

    def test_one_image_decoded_once_for_its_page_count(self):
        from pydicom.uid import JPEGLossless

        file_object = make_dicom(
            columns=16, frames=(JPEG_PREDICTOR_1,), rows=12,
            transfer_syntax=JPEGLossless
        )
        with mock.patch.object(dicom, '_decode_frame') as decoder:
            self.assertEqual(dicom.get_dicom_page_count(file_object=file_object), 1)
        decoder.assert_not_called()

    def test_decoder_of_the_project_without_other_plugin(self):
        from pydicom.pixels.decoders import JPEGLosslessDecoder

        jpeg_lossless.register_decoder()
        self.assertIn(
            jpeg_lossless.PLUGIN_LABEL, JPEGLosslessDecoder.available_plugins
        )
