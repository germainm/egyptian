"""
Decoder of the sequential JPEG images (SOF0 and SOF1) with samples of 8 or 12
bits: the DICOM transfer syntax "JPEG Extended" (processes 2 and 4).

Pillow and the GDCM plugin of pydicom refuse the samples of 12 bits, and the
remaining plugin of pydicom, pylibjpeg-libjpeg, is under the GPLv3, which cannot
be combined with this project (GPL-2.0-only). This module is part of the project
and needs nothing that reading DICOM pixels does not already need: numpy.

The inverse DCT is the integer form of the algorithm of Loeffler, Ligtenberg
and Moschytz (1989), scaled as in the "slow integer" method of libjpeg of the
Independent JPEG Group. The components with fewer samples than the others are
enlarged by the same filter as libjpeg-turbo by default: a triangle over the
neighbors for twice the samples, repetition for the other factors. The results
are those of libjpeg-turbo.

The data comes from outside: images are limited in pixels and in time, a file
too short to hold the image it declares is refused, an error in the
entropy-coded data leaves the rest of its segment in gray.
"""
from array import array
from importlib.util import find_spec
import logging
import re
import time

logger = logging.getLogger(name=__name__)

PIXELS_MAXIMUM = 64000000
TIME_MAXIMUM = 120

PLUGIN_LABEL = 'egyptian'
UID_JPEG_EXTENDED = '1.2.840.10008.1.2.4.51'
# The plugin interface of pydicom.
DECODER_DEPENDENCIES = {UID_JPEG_EXTENDED: ('numpy',)}

MARKER_DHT = 0xC4
MARKER_DNL = 0xDC
MARKER_DQT = 0xDB
MARKER_DRI = 0xDD
MARKER_EOI = 0xD9
MARKER_SOF_SEQUENTIAL = (0xC0, 0xC1)
MARKER_SOF_UNSUPPORTED = {
    0xC2: 'progressive', 0xC3: 'lossless', 0xC5: 'hierarchical',
    0xC6: 'hierarchical', 0xC7: 'hierarchical', 0xC9: 'arithmetic',
    0xCA: 'arithmetic', 0xCB: 'arithmetic', 0xCD: 'arithmetic',
    0xCE: 'arithmetic', 0xCF: 'arithmetic'
}
MARKER_SOS = 0xDA

REGEX_END_OF_SCAN = re.compile(pattern=b'\xff[^\x00\xd0-\xd7\xff]')
REGEX_RESTART = re.compile(pattern=b'\xff\xff*[\xd0-\xd7]')

ZIGZAG = (
    0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5, 12, 19, 26, 33,
    40, 48, 41, 34, 27, 20, 13, 6, 7, 14, 21, 28, 35, 42, 49, 56, 57, 50, 43,
    36, 29, 22, 15, 23, 30, 37, 44, 51, 58, 59, 52, 45, 38, 31, 39, 46, 53,
    60, 61, 54, 47, 55, 62, 63
)

# The constants of the transform, multiplied by 2 ** 13.
CONSTANT_BITS = 13
FIX_0_298631336 = 2446
FIX_0_390180644 = 3196
FIX_0_541196100 = 4433
FIX_0_765366865 = 6270
FIX_0_899976223 = 7373
FIX_1_175875602 = 9633
FIX_1_501321110 = 12299
FIX_1_847759065 = 15137
FIX_1_961570560 = 16069
FIX_2_053119869 = 16819
FIX_2_562915447 = 20995
FIX_3_072711026 = 25172
# The constants of the YCbCr to RGB conversion, multiplied by 2 ** 16.
FIX_0_34414 = 22554
FIX_0_71414 = 46802
FIX_1_402 = 91881
FIX_1_772 = 116130


class JPEGDecodeError(ValueError):
    """The image cannot be decoded by this module."""


class DamagedSegment(Exception):
    """The entropy-coded data of a segment holds an invalid code."""


class Component:
    def __init__(self, identifier, horizontal, vertical, quantization):
        self.blocks_high = 0
        self.blocks_wide = 0
        self.coefficients = None
        self.horizontal = horizontal
        self.identifier = identifier
        self.quantization = quantization
        self.vertical = vertical


class Frame:
    def __init__(self, components, columns, data_size, precision, rows):
        self.columns = columns
        self.components = components
        self.horizontal_maximum = max(item.horizontal for item in components)
        self.precision = precision
        self.rows = rows
        self.vertical_maximum = max(item.vertical for item in components)
        self.mcus_wide = _divide_up(columns, 8 * self.horizontal_maximum)
        self.mcus_high = _divide_up(rows, 8 * self.vertical_maximum)

        # Each block takes at least two bits, a DC code and an end of block
        # code, and the coefficients are allocated from the declared size.
        blocks = self.mcus_wide * self.mcus_high * sum(
            item.horizontal * item.vertical for item in components
        )
        if data_size * 8 < blocks * 2:
            raise JPEGDecodeError(
                'file too short for an image of {} by {}'.format(columns, rows)
            )

        for component in components:
            if (
                self.horizontal_maximum % component.horizontal or
                self.vertical_maximum % component.vertical
            ):
                raise JPEGDecodeError('fractional sampling factors')

            component.blocks_wide = self.mcus_wide * component.horizontal
            component.blocks_high = self.mcus_high * component.vertical
            component.coefficients = array(
                'i', bytes(
                    4 * 64 * component.blocks_wide * component.blocks_high
                )
            )


def _divide_up(value, divisor):
    return (value + divisor - 1) // divisor


def stop_if_late(deadline):
    if time.monotonic() > deadline:
        raise JPEGDecodeError(
            'not decoded after {} seconds'.format(TIME_MAXIMUM)
        )


def split_scan(data):
    """The segments of a scan, between its restart markers."""
    return REGEX_RESTART.split(data)


def read_segments(data, deadline):
    """
    The marker of each segment of the file, its content and, for a scan, the
    entropy-coded data that follow its header.
    """
    if data[:2] != b'\xff\xd8':
        raise JPEGDecodeError('no JPEG start of image')

    position = 2
    while position + 1 < len(data):
        if data[position] != 0xFF or data[position + 1] in (0x00, 0xFF):
            position += 1
            continue

        marker = data[position + 1]
        position += 2
        if marker == MARKER_EOI:
            return
        if 0xD0 <= marker <= 0xD8:
            continue

        # A file can hold any number of tables, each one takes time.
        stop_if_late(deadline=deadline)

        size = int.from_bytes(data[position:position + 2], 'big')
        segment = data[position + 2:position + size]
        position += size

        if marker == MARKER_SOS:
            match = REGEX_END_OF_SCAN.search(data, position)
            end = match.start() if match else len(data)
            yield marker, segment, data[position:end]
            position = end
        else:
            yield marker, segment, b''


def _read_quantization_tables(segment, tables):
    position = 0
    while position < len(segment):
        precision, identifier = segment[position] >> 4, segment[position] & 15
        position += 1
        size = 2 if precision else 1
        values = segment[position:position + 64 * size]
        if len(values) != 64 * size:
            raise JPEGDecodeError('short quantization table')
        position += 64 * size

        table = [0] * 64
        for index in range(64):
            table[ZIGZAG[index]] = int.from_bytes(
                values[index * size:(index + 1) * size], 'big'
            )
        tables[identifier] = table


def read_huffman_tables(segment, tables):
    """
    Each table has one entry per value of the next 16 bits: the symbol
    multiplied by 256 plus the length of its code, 0 for an invalid code.
    """
    position = 0
    while position < len(segment):
        key = segment[position]
        counts = segment[position + 1:position + 17]
        total = sum(counts)
        symbols = segment[position + 17:position + 17 + total]
        if len(counts) != 16 or len(symbols) != total:
            raise JPEGDecodeError('short Huffman table')
        position += 17 + total

        table = [0] * 65536
        code = 0
        index = 0
        for length, count in enumerate(counts, start=1):
            span = 1 << (16 - length)
            for _ in range(count):
                start = code << (16 - length)
                if start + span > 65536:
                    raise JPEGDecodeError('invalid Huffman table')
                table[start:start + span] = [
                    (symbols[index] << 8) | length
                ] * span
                code += 1
                index += 1
            code <<= 1
        tables[key] = table


def _read_frame(segment, data_size):
    if len(segment) < 6:
        raise JPEGDecodeError('short frame header')

    precision = segment[0]
    rows = int.from_bytes(segment[1:3], 'big')
    columns = int.from_bytes(segment[3:5], 'big')
    count = segment[5]
    if precision not in (8, 12):
        raise JPEGDecodeError('samples of {} bits'.format(precision))
    if not rows or not columns:
        raise JPEGDecodeError('image without height or width')
    if not count or count > 4 or len(segment) < 6 + 3 * count:
        raise JPEGDecodeError('invalid number of components')
    if rows * columns * count > PIXELS_MAXIMUM:
        raise JPEGDecodeError(
            'image larger than {} samples'.format(PIXELS_MAXIMUM)
        )

    components = []
    for index in range(count):
        identifier, sampling, quantization = segment[6 + 3 * index:9 + 3 * index]
        horizontal, vertical = sampling >> 4, sampling & 15
        if not 1 <= horizontal <= 4 or not 1 <= vertical <= 4:
            raise JPEGDecodeError('invalid sampling factors')
        components.append(
            Component(
                horizontal=horizontal, identifier=identifier,
                quantization=quantization, vertical=vertical
            )
        )

    return Frame(
        columns=columns, components=components, data_size=data_size,
        precision=precision, rows=rows
    )


def _scan_plan(frame, segment, tables_huffman):
    """Components of the scan with the position of their blocks in a MCU."""
    if not segment or len(segment) < 1 + 2 * segment[0]:
        raise JPEGDecodeError('short scan header')

    plan = []
    count = segment[0]
    if not 1 <= count <= 4:
        raise JPEGDecodeError('invalid number of components in a scan')

    for index in range(count):
        identifier, selectors = segment[1 + 2 * index:3 + 2 * index]
        for component in frame.components:
            if component.identifier == identifier:
                break
        else:
            raise JPEGDecodeError('scan of an unknown component')

        try:
            table_dc = tables_huffman[selectors >> 4]
            table_ac = tables_huffman[16 | (selectors & 15)]
        except KeyError:
            raise JPEGDecodeError('missing Huffman table')

        if count == 1:
            # Not interleaved: a MCU is a block, on the rows and columns of
            # blocks that the samples of the component need.
            samples_wide = _divide_up(
                frame.columns * component.horizontal, frame.horizontal_maximum
            )
            samples_high = _divide_up(
                frame.rows * component.vertical, frame.vertical_maximum
            )
            mcus_wide = _divide_up(samples_wide, 8)
            mcus_high = _divide_up(samples_high, 8)
            steps = (1, 1)
        else:
            mcus_wide = frame.mcus_wide
            mcus_high = frame.mcus_high
            steps = (component.horizontal, component.vertical)

        plan.append(
            (
                component, table_dc, table_ac, steps[0], steps[1],
                tuple(
                    (horizontal, vertical)
                    for vertical in range(steps[1])
                    for horizontal in range(steps[0])
                )
            )
        )

    return plan, mcus_wide, mcus_high


def _decode_scan(plan, mcus_wide, mcus_high, segments, restart_interval, deadline):
    """Fill the coefficients of the components; return the MCU decoded."""
    mcus = mcus_wide * mcus_high
    mcu = 0
    decoded = 0
    damaged = 0
    plan_size = len(plan)
    zigzag = ZIGZAG

    for segment in segments:
        if mcu >= mcus:
            break

        data = segment.replace(b'\xff\x00', b'\xff')
        size_bits = len(data) * 8
        position = 0
        accumulator = 0
        bits = 0
        predictions = [0] * plan_size
        limit = min(mcus, mcu + restart_interval) if restart_interval else mcus

        try:
            while mcu < limit:
                if position * 8 - bits >= size_bits:
                    raise DamagedSegment
                if not mcu % 4096:
                    stop_if_late(deadline=deadline)

                row, column = divmod(mcu, mcus_wide)
                for index in range(plan_size):
                    component, table_dc, table_ac, step_h, step_v, blocks = plan[index]
                    coefficients = component.coefficients
                    stride = component.blocks_wide
                    prediction = predictions[index]

                    for horizontal, vertical in blocks:
                        offset = 64 * (
                            (row * step_v + vertical) * stride +
                            column * step_h + horizontal
                        )

                        if bits < 32:
                            accumulator = (
                                (accumulator & ((1 << bits) - 1)) << 48
                            ) | int.from_bytes(
                                data[position:position + 6].ljust(6, b'\x00'), 'big'
                            )
                            position += 6
                            bits += 48

                        entry = table_dc[(accumulator >> (bits - 16)) & 65535]
                        if not entry:
                            raise DamagedSegment
                        bits -= entry & 255
                        size = entry >> 8
                        if size:
                            if size > 16:
                                raise DamagedSegment
                            bits -= size
                            value = (accumulator >> bits) & ((1 << size) - 1)
                            if value < 1 << (size - 1):
                                value -= (1 << size) - 1
                            prediction += value
                        coefficients[offset] = prediction

                        coefficient = 1
                        while coefficient < 64:
                            if bits < 32:
                                accumulator = (
                                    (accumulator & ((1 << bits) - 1)) << 48
                                ) | int.from_bytes(
                                    data[position:position + 6].ljust(6, b'\x00'), 'big'
                                )
                                position += 6
                                bits += 48

                            entry = table_ac[(accumulator >> (bits - 16)) & 65535]
                            if not entry:
                                raise DamagedSegment
                            bits -= entry & 255
                            symbol = entry >> 8
                            size = symbol & 15
                            if size:
                                coefficient += symbol >> 4
                                if coefficient > 63:
                                    raise DamagedSegment
                                bits -= size
                                value = (accumulator >> bits) & ((1 << size) - 1)
                                if value < 1 << (size - 1):
                                    value -= (1 << size) - 1
                                coefficients[offset + zigzag[coefficient]] = value
                                coefficient += 1
                            elif symbol == 0xF0:
                                coefficient += 16
                            else:
                                break

                    predictions[index] = prediction

                mcu += 1
                decoded += 1
        except (DamagedSegment, OverflowError):
            damaged += 1
            if restart_interval:
                # The next segment starts at its own place in the image.
                mcu = limit

    if damaged:
        logger.warning(
            'JPEG data damaged or incomplete: %d of %d MCU decoded',
            decoded, mcus
        )

    return decoded


def _transform(v0, v1, v2, v3, v4, v5, v6, v7, shift):
    # Even part.
    z1 = (v2 + v6) * FIX_0_541196100
    t2 = z1 - v6 * FIX_1_847759065
    t3 = z1 + v2 * FIX_0_765366865
    t0 = (v0 + v4) << CONSTANT_BITS
    t1 = (v0 - v4) << CONSTANT_BITS
    t10 = t0 + t3
    t13 = t0 - t3
    t11 = t1 + t2
    t12 = t1 - t2

    # Odd part.
    z1 = v7 + v1
    z2 = v5 + v3
    z3 = v7 + v3
    z4 = v5 + v1
    z5 = (z3 + z4) * FIX_1_175875602
    z1 = z1 * -FIX_0_899976223
    z2 = z2 * -FIX_2_562915447
    z3 = z3 * -FIX_1_961570560 + z5
    z4 = z4 * -FIX_0_390180644 + z5
    o0 = v7 * FIX_0_298631336 + z1 + z3
    o1 = v5 * FIX_2_053119869 + z2 + z4
    o2 = v3 * FIX_3_072711026 + z2 + z3
    o3 = v1 * FIX_1_501321110 + z1 + z4

    half = 1 << (shift - 1)
    return (
        (t10 + o3 + half) >> shift, (t11 + o2 + half) >> shift,
        (t12 + o1 + half) >> shift, (t13 + o0 + half) >> shift,
        (t13 - o0 + half) >> shift, (t12 - o1 + half) >> shift,
        (t11 - o2 + half) >> shift, (t10 - o3 + half) >> shift
    )


def _inverse_dct(blocks, precision):
    """Samples of blocks of the shape (count, 8, 8), level shifted."""
    import numpy

    # Bits kept between the two passes: less for 12-bit samples, for the
    # intermediate values to stay in 32 bits as in the original method.
    pass_bits = 1 if precision == 12 else 2

    columns = _transform(
        *(blocks[:, index, :] for index in range(8)),
        shift=CONSTANT_BITS - pass_bits
    )
    rows = _transform(
        *(
            numpy.stack([column[:, index] for column in columns], axis=1)
            for index in range(8)
        ), shift=CONSTANT_BITS + pass_bits + 3
    )
    samples = numpy.stack(rows, axis=2) + (1 << (precision - 1))
    return numpy.clip(samples, 0, (1 << precision) - 1)


def _double_columns(samples, shift, bias_left, bias_right):
    """
    Two samples for each one along the rows: three quarters of it and a quarter
    of its neighbor on that side. The samples at the ends have no neighbor on
    their outer side and count for all of it.
    """
    import numpy

    result = numpy.empty(
        (samples.shape[0], samples.shape[1] * 2), dtype=numpy.int32
    )
    result[:, 0] = (samples[:, 0] * 4 + bias_left) >> shift
    result[:, 1:-1:2] = (
        samples[:, :-1] * 3 + samples[:, 1:] + bias_right
    ) >> shift
    result[:, 2::2] = (
        samples[:, 1:] * 3 + samples[:, :-1] + bias_left
    ) >> shift
    result[:, -1] = (samples[:, -1] * 4 + bias_right) >> shift
    return result


def _enlarge(samples, factor_horizontal, factor_vertical):
    """
    The samples of a component multiplied along the rows and the columns, by
    the filter that libjpeg-turbo chooses for these factors and this width. The
    bias alternates so that the rounding does not move the values one way.
    """
    import numpy

    wide_enough = samples.shape[1] > 2

    if factor_horizontal == 2 and factor_vertical == 1 and wide_enough:
        return _double_columns(
            samples=samples.astype(numpy.int32), shift=2, bias_left=1,
            bias_right=2
        ).astype(numpy.uint16)

    if factor_vertical == 2 and (
        factor_horizontal == 1 or (factor_horizontal == 2 and wide_enough)
    ):
        samples = samples.astype(numpy.int32)
        # The rows at the ends are their own neighbors outside the image.
        above = samples * 3 + numpy.concatenate((samples[:1], samples[:-1]))
        below = samples * 3 + numpy.concatenate((samples[1:], samples[-1:]))
        if factor_horizontal == 1:
            result = numpy.empty(
                (samples.shape[0] * 2, samples.shape[1]), dtype=numpy.int32
            )
            result[0::2] = (above + 1) >> 2
            result[1::2] = (below + 2) >> 2
        else:
            result = numpy.empty(
                (samples.shape[0] * 2, samples.shape[1] * 2), dtype=numpy.int32
            )
            result[0::2] = _double_columns(
                samples=above, shift=4, bias_left=8, bias_right=7
            )
            result[1::2] = _double_columns(
                samples=below, shift=4, bias_left=8, bias_right=7
            )
        return result.astype(numpy.uint16)

    return samples.repeat(factor_horizontal, axis=1).repeat(
        factor_vertical, axis=0
    )


def _component_samples(frame, component, table):
    """The samples of a component, at the size of the image."""
    import numpy

    coefficients = numpy.frombuffer(
        component.coefficients, dtype=numpy.intc
    ).reshape(component.blocks_high, component.blocks_wide, 8, 8)
    quantization = numpy.array(table, dtype=numpy.int64).reshape(8, 8)

    samples = numpy.empty(
        (component.blocks_high * 8, component.blocks_wide * 8),
        dtype=numpy.uint16
    )
    for row in range(component.blocks_high):
        result = _inverse_dct(
            blocks=coefficients[row].astype(numpy.int64) * quantization,
            precision=frame.precision
        )
        samples[row * 8:(row + 1) * 8] = result.transpose(1, 0, 2).reshape(
            8, component.blocks_wide * 8
        )

    factor_horizontal = frame.horizontal_maximum // component.horizontal
    factor_vertical = frame.vertical_maximum // component.vertical
    if factor_horizontal > 1 or factor_vertical > 1:
        # The filters must see the edge of the image, not the rest of the block.
        samples = _enlarge(
            samples=samples[
                :_divide_up(
                    frame.rows * component.vertical, frame.vertical_maximum
                ), :_divide_up(
                    frame.columns * component.horizontal,
                    frame.horizontal_maximum
                )
            ], factor_horizontal=factor_horizontal,
            factor_vertical=factor_vertical
        )

    return samples[:frame.rows, :frame.columns]


def decode_jpeg(data):
    """
    Return the samples of the image as an array of unsigned integers of the
    shape (rows, columns, components) and their precision in bits. The
    samples are the coded ones: YCbCr samples are not converted to RGB.
    """
    import numpy

    deadline = time.monotonic() + TIME_MAXIMUM
    decoded = 0
    frame = None
    restart_interval = 0
    tables_huffman = {}
    tables_quantization = {}

    for marker, segment, entropy_data in read_segments(
        data=data, deadline=deadline
    ):
        if marker == MARKER_DQT:
            _read_quantization_tables(segment, tables_quantization)
        elif marker == MARKER_DHT:
            read_huffman_tables(segment, tables_huffman)
        elif marker == MARKER_DRI:
            restart_interval = int.from_bytes(segment[:2], 'big')
        elif marker == MARKER_DNL:
            raise JPEGDecodeError('number of lines after the scan')
        elif marker in MARKER_SOF_UNSUPPORTED:
            raise JPEGDecodeError(
                '{} JPEG'.format(MARKER_SOF_UNSUPPORTED[marker])
            )
        elif marker in MARKER_SOF_SEQUENTIAL:
            if frame:
                raise JPEGDecodeError('several frames')
            frame = _read_frame(segment=segment, data_size=len(data))
        elif marker == MARKER_SOS:
            if not frame:
                raise JPEGDecodeError('scan before the frame header')

            plan, mcus_wide, mcus_high = _scan_plan(
                frame=frame, segment=segment, tables_huffman=tables_huffman
            )
            decoded += _decode_scan(
                deadline=deadline, mcus_high=mcus_high, mcus_wide=mcus_wide,
                plan=plan, restart_interval=restart_interval,
                segments=split_scan(entropy_data)
            )

    if not frame:
        raise JPEGDecodeError('no frame header')
    if not decoded:
        raise JPEGDecodeError('no image data')

    planes = []
    for component in frame.components:
        try:
            table = tables_quantization[component.quantization]
        except KeyError:
            raise JPEGDecodeError('missing quantization table')
        planes.append(
            _component_samples(frame=frame, component=component, table=table)
        )

    return numpy.stack(planes, axis=2), frame.precision


def _ybr_to_rgb(samples, precision):
    """
    The conversion of JFIF, in integers as in libjpeg: pydicom only converts
    samples of 8 bits.
    """
    import numpy

    center = 1 << (precision - 1)
    luma = samples[:, :, 0].astype(numpy.int64)
    blue = samples[:, :, 1].astype(numpy.int64) - center
    red = samples[:, :, 2].astype(numpy.int64) - center
    half = 1 << 15

    return numpy.clip(
        numpy.stack(
            (
                luma + ((FIX_1_402 * red + half) >> 16),
                luma + ((-FIX_0_34414 * blue - FIX_0_71414 * red + half) >> 16),
                luma + ((FIX_1_772 * blue + half) >> 16)
            ), axis=2
        ), 0, (1 << precision) - 1
    )


def get_frame_bytes(samples, precision, runner):
    """The samples as pydicom expects them from a plugin."""
    import numpy

    if samples.shape != (runner.rows, runner.columns, runner.samples_per_pixel):
        raise JPEGDecodeError(
            'image of {} in a DICOM file that declares {}'.format(
                samples.shape,
                (runner.rows, runner.columns, runner.samples_per_pixel)
            )
        )

    if runner.samples_per_pixel > 1:
        runner.set_option('planar_configuration', 0)
        if runner.photometric_interpretation in ('YBR_FULL', 'YBR_FULL_422'):
            samples = _ybr_to_rgb(samples=samples, precision=precision)
            runner.set_option('photometric_interpretation', 'RGB')

    bits_allocated = runner.bits_allocated
    if precision > bits_allocated:
        bits_allocated = 16
        runner.set_option('bits_allocated', bits_allocated)
        runner.set_option('bits_stored', precision)

    if runner.pixel_representation == 1:
        # Two's complement over the precision of the samples.
        samples = samples.astype(numpy.int32)
        samples[samples >= 1 << (precision - 1)] -= 1 << precision
        data_type = '<i2' if bits_allocated == 16 else 'i1'
    else:
        data_type = '<u2' if bits_allocated == 16 else 'u1'

    return samples.astype(data_type).tobytes()


def decode_frame(src, runner):
    """Plugin function of pydicom: the bytes of a frame."""
    samples, precision = decode_jpeg(data=src)
    return get_frame_bytes(precision=precision, runner=runner, samples=samples)


def is_available(uid):
    """Plugin function of pydicom."""
    return uid in DECODER_DEPENDENCIES and find_spec('numpy') is not None


def register_decoder():
    """Add the plugin to the JPEG Extended decoder of pydicom, once."""
    from pydicom.pixels.decoders import JPEGExtended12BitDecoder

    if PLUGIN_LABEL not in JPEGExtended12BitDecoder.available_plugins:
        try:
            JPEGExtended12BitDecoder.add_plugin(
                PLUGIN_LABEL, (__name__, 'decode_frame')
            )
        except ValueError:
            """Added by another thread in the meantime."""
    return PLUGIN_LABEL
