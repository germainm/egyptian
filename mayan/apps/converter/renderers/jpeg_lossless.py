"""
Decoder of the lossless JPEG images (SOF3, Huffman coding): the DICOM transfer
syntaxes "JPEG Lossless" (process 14, all the predictors) and "JPEG Lossless,
Selection Value 1". The remaining plugin of pydicom for them, pylibjpeg-libjpeg,
is under the GPLv3, which cannot be combined with this project (GPL-2.0-only).

Written from the standard (ITU-T T.81, annex H). The differences are read with
a Python loop; the samples are then computed by numpy, a row at a time, except
for the predictors 6 and 7, where each sample needs the result of the previous
one in the form of a shift.

The data comes from outside: same limits as jpeg_extended.py.
"""
from importlib.util import find_spec
from array import array
from itertools import cycle
import logging
import time

from .jpeg_extended import (
    DamagedSegment, JPEGDecodeError, MARKER_DHT, MARKER_DNL, MARKER_DRI,
    MARKER_SOF_SEQUENTIAL, MARKER_SOF_UNSUPPORTED, MARKER_SOS, PIXELS_MAXIMUM,
    PLUGIN_LABEL, TIME_MAXIMUM, get_frame_bytes, read_huffman_tables,
    read_segments, split_scan, stop_if_late
)

logger = logging.getLogger(name=__name__)

MARKER_SOF_LOSSLESS = 0xC3
SAMPLE_MASK = 65535
# Size of a difference that has no additional bits.
SIZE_MAXIMUM = 16

UID_JPEG_LOSSLESS = '1.2.840.10008.1.2.4.57'
UID_JPEG_LOSSLESS_SV1 = '1.2.840.10008.1.2.4.70'
# The plugin interface of pydicom.
DECODER_DEPENDENCIES = {
    UID_JPEG_LOSSLESS: ('numpy',), UID_JPEG_LOSSLESS_SV1: ('numpy',)
}


class Frame:
    def __init__(self, segment, data_size):
        if len(segment) < 6:
            raise JPEGDecodeError('short frame header')

        self.precision = segment[0]
        self.rows = int.from_bytes(segment[1:3], 'big')
        self.columns = int.from_bytes(segment[3:5], 'big')
        count = segment[5]
        if not 2 <= self.precision <= 16:
            raise JPEGDecodeError('samples of {} bits'.format(self.precision))
        if not self.rows or not self.columns:
            raise JPEGDecodeError('image without height or width')
        if not count or count > 4 or len(segment) < 6 + 3 * count:
            raise JPEGDecodeError('invalid number of components')

        total = self.rows * self.columns * count
        if total > PIXELS_MAXIMUM:
            raise JPEGDecodeError(
                'image larger than {} samples'.format(PIXELS_MAXIMUM)
            )
        # Each sample takes at least one bit, and memory is allocated from
        # the declared size.
        if data_size * 8 < total:
            raise JPEGDecodeError(
                'file too short for an image of {} by {}'.format(
                    self.columns, self.rows
                )
            )

        self.identifiers = [segment[6 + 3 * index] for index in range(count)]
        if count > 1 and any(
            segment[7 + 3 * index] != 0x11 for index in range(count)
        ):
            raise JPEGDecodeError('subsampled lossless JPEG')

        self.planes = {}


def _read_differences(
    columns, count, deadline, restart_interval, segments, tables
):
    """
    The differences of a scan, in the order of the file. A restart interval
    is counted in samples here.
    """
    differences = array('i', bytes(4 * count))
    index = 0
    damaged = 0
    decoded = 0
    tables = cycle(tables)
    mask = SAMPLE_MASK

    for segment in segments:
        if index >= count:
            break

        data = segment.replace(b'\xff\x00', b'\xff')
        size_bits = len(data) * 8
        position = 0
        accumulator = 0
        bits = 0
        limit = min(count, index + restart_interval) if restart_interval else count

        try:
            for row_start in range(index, limit, columns):
                stop_if_late(deadline=deadline)
                if position * 8 - bits >= size_bits:
                    raise DamagedSegment

                for index, table in zip(
                    range(row_start, min(row_start + columns, limit)), tables
                ):
                    if bits < 32:
                        accumulator = (
                            (accumulator & ((1 << bits) - 1)) << 48
                        ) | int.from_bytes(
                            data[position:position + 6].ljust(6, b'\x00'), 'big'
                        )
                        position += 6
                        bits += 48

                    entry = table[(accumulator >> (bits - 16)) & mask]
                    if not entry:
                        raise DamagedSegment
                    bits -= entry & 255
                    size = entry >> 8
                    if size:
                        if size >= SIZE_MAXIMUM:
                            if size > SIZE_MAXIMUM:
                                raise DamagedSegment
                            value = 32768
                        else:
                            bits -= size
                            value = (accumulator >> bits) & ((1 << size) - 1)
                            if value < 1 << (size - 1):
                                value -= (1 << size) - 1
                        differences[index] = value
                    decoded += 1

            index = limit
        except DamagedSegment:
            damaged += 1
            # The next segment starts at its own place in the image.
            index = limit if restart_interval else index

    if damaged:
        logger.warning(
            'JPEG data damaged or incomplete: %d of %d samples decoded',
            decoded, count
        )

    if not decoded:
        raise JPEGDecodeError('no image data')

    return differences


def _next_row(values, previous, predictor):
    """
    The samples of a row from its differences (which this function changes)
    and from the row above, with the first sample predicted from the row above
    whatever the predictor is.
    """
    import numpy

    values[0] += previous[0]

    if predictor == 1:
        return numpy.cumsum(values) & SAMPLE_MASK
    if predictor == 2:
        values[1:] += previous[1:]
        return values & SAMPLE_MASK
    if predictor == 3:
        values[1:] += previous[:-1]
        return values & SAMPLE_MASK
    if predictor == 4:
        values[1:] += previous[1:] - previous[:-1]
        return numpy.cumsum(values) & SAMPLE_MASK
    if predictor == 5:
        values[1:] += (previous[1:] - previous[:-1]) >> 1
        return numpy.cumsum(values) & SAMPLE_MASK

    above = previous.tolist()
    result = values.tolist()
    left = result[0] & SAMPLE_MASK
    result[0] = left
    if predictor == 6:
        for index in range(1, len(result)):
            left = (
                result[index] + above[index] + ((left - above[index - 1]) >> 1)
            ) & SAMPLE_MASK
            result[index] = left
    else:
        for index in range(1, len(result)):
            left = (result[index] + ((left + above[index]) >> 1)) & SAMPLE_MASK
            result[index] = left

    return numpy.array(result, dtype=numpy.int64)


def _get_plane(differences, deadline, predictor, restart_rows, transform, initial):
    """The samples of a component from its differences."""
    import numpy

    rows, columns = differences.shape
    plane = numpy.empty((rows, columns), dtype=numpy.uint16)
    previous = None

    for row in range(rows):
        if not row % 256:
            stop_if_late(deadline=deadline)

        values = differences[row].astype(numpy.int64)
        if previous is None or (restart_rows and not row % restart_rows):
            # The first row of the image and of each restart interval are
            # predicted from the left only.
            values[0] += initial
            previous = numpy.cumsum(values) & SAMPLE_MASK
        else:
            previous = _next_row(
                predictor=predictor, previous=previous, values=values
            )
        plane[row] = (previous << transform) & SAMPLE_MASK

    return plane


def _decode_scan(frame, segment, entropy_data, tables, restart_interval, deadline):
    import numpy

    if not segment or len(segment) < 4 + 2 * segment[0]:
        raise JPEGDecodeError('short scan header')

    count = segment[0]
    if not 1 <= count <= len(frame.identifiers):
        raise JPEGDecodeError('invalid number of components in a scan')

    predictor = segment[1 + 2 * count]
    transform = segment[3 + 2 * count] & 15
    if not 1 <= predictor <= 7:
        raise JPEGDecodeError('predictor {}'.format(predictor))
    if transform >= frame.precision:
        raise JPEGDecodeError('invalid point transform')

    identifiers = []
    scan_tables = []
    for index in range(count):
        identifier, selectors = segment[1 + 2 * index:3 + 2 * index]
        if identifier not in frame.identifiers:
            raise JPEGDecodeError('scan of an unknown component')
        try:
            scan_tables.append(tables[selectors >> 4])
        except KeyError:
            raise JPEGDecodeError('missing Huffman table')
        identifiers.append(identifier)

    restart_rows = 0
    if restart_interval:
        # Whole rows, for the first row of an interval to be a row of its own.
        restart_rows, remainder = divmod(restart_interval, frame.columns)
        if remainder or not restart_rows:
            raise JPEGDecodeError(
                'restart interval that is not a number of rows'
            )

    differences = numpy.frombuffer(
        _read_differences(
            columns=frame.columns * count, count=frame.rows * frame.columns * count,
            deadline=deadline, restart_interval=restart_interval * count,
            segments=split_scan(entropy_data), tables=scan_tables
        ), dtype=numpy.intc
    ).reshape(frame.rows, frame.columns, count)

    initial = 1 << (frame.precision - transform - 1)
    for index, identifier in enumerate(identifiers):
        frame.planes[identifier] = _get_plane(
            deadline=deadline, differences=differences[:, :, index],
            initial=initial, predictor=predictor, restart_rows=restart_rows,
            transform=transform
        )


def decode_jpeg_lossless(data):
    """
    Return the samples of the image as an array of unsigned integers of the
    shape (rows, columns, components) and their precision in bits.
    """
    import numpy

    deadline = time.monotonic() + TIME_MAXIMUM
    frame = None
    restart_interval = 0
    tables = {}

    for marker, segment, entropy_data in read_segments(
        data=data, deadline=deadline
    ):
        if marker == MARKER_DHT:
            read_huffman_tables(segment, tables)
        elif marker == MARKER_DRI:
            restart_interval = int.from_bytes(segment[:2], 'big')
        elif marker == MARKER_DNL:
            raise JPEGDecodeError('number of lines after the scan')
        elif marker == MARKER_SOF_LOSSLESS:
            if frame:
                raise JPEGDecodeError('several frames')
            frame = Frame(segment=segment, data_size=len(data))
        elif marker in MARKER_SOF_SEQUENTIAL:
            raise JPEGDecodeError('sequential JPEG, not a lossless one')
        elif marker in MARKER_SOF_UNSUPPORTED:
            raise JPEGDecodeError(
                '{} JPEG'.format(MARKER_SOF_UNSUPPORTED[marker])
            )
        elif marker == MARKER_SOS:
            if not frame:
                raise JPEGDecodeError('scan before the frame header')
            _decode_scan(
                deadline=deadline, entropy_data=entropy_data, frame=frame,
                restart_interval=restart_interval, segment=segment,
                tables=tables
            )

    if not frame:
        raise JPEGDecodeError('no frame header')

    try:
        planes = [frame.planes[item] for item in frame.identifiers]
    except KeyError:
        raise JPEGDecodeError('no image data')

    return numpy.stack(planes, axis=2), frame.precision


def decode_frame(src, runner):
    """Plugin function of pydicom: the bytes of a frame."""
    samples, precision = decode_jpeg_lossless(data=src)
    return get_frame_bytes(precision=precision, runner=runner, samples=samples)


def is_available(uid):
    """Plugin function of pydicom."""
    return uid in DECODER_DEPENDENCIES and find_spec('numpy') is not None


def register_decoder():
    """Add the plugin to the lossless JPEG decoders of pydicom, once."""
    from pydicom.pixels.decoders import (
        JPEGLosslessDecoder, JPEGLosslessSV1Decoder
    )

    for decoder in (JPEGLosslessDecoder, JPEGLosslessSV1Decoder):
        if PLUGIN_LABEL not in decoder.available_plugins:
            try:
                decoder.add_plugin(PLUGIN_LABEL, (__name__, 'decode_frame'))
            except ValueError:
                """Added by another thread in the meantime."""
