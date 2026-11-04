"""
Decoder of the lossless JPEG images (SOF3, Huffman coding): the DICOM transfer
syntaxes "JPEG Lossless" (process 14, all the predictors) and "JPEG Lossless,
Selection Value 1". The remaining plugin of pydicom for them, pylibjpeg-libjpeg,
is under the GPLv3, which cannot be combined with this project (GPL-2.0-only).

Written from the standard (ITU-T T.81, annex H).

A code of a Huffman stream can only be found from the end of the previous one,
which looks like a loop that numpy cannot help with. But such streams
resynchronize: a reader that starts at a wrong bit soon falls on the boundaries
of the right codes (Klein and Wiseman, "Parallel Huffman decoding", 2000). So
thousands of readers start along the stream and advance together, in arrays,
in two passes. The first one counts the differences of each reader and checks
that it ends exactly on the first bit of the next reader, which makes the
result independent of any probability: by induction from the first bit of the
stream, each reader is on the right codes. The second one writes the
differences at their place.

Everything unusual goes to the Python loop, which defines the behavior: invalid
codes, truncated data, a stream that does not resynchronize, a scan with several
Huffman tables.

The samples are then computed by numpy, a row at a time. The predictors 6 and 7
do not allow it, as each sample needs the one on its left in the form of a
shift: they go a diagonal at a time, whose samples only need the two diagonals
before.

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
# The longest difference: a code of 16 bits and 15 additional bits.
DIFFERENCE_BITS_MAXIMUM = 31
# In the table of the differences: the next 16 bits do not hold it whole.
DIFFERENCE_LONG = 1 << 20

# Segments with fewer samples go to the Python loop: arrays cost more than they
# save (measured: the same time for 128 by 128).
READERS_SAMPLES_MINIMUM = 16384
# Bits between the starting points of the readers, and how many of them.
READERS_SPACING_MINIMUM = 2048
READERS_SPACING_SHIFT = 14
# Differences that a reader reads to resynchronize before its part begins.
READERS_SYNCHRONIZATION = 64
# Share of the readers that may fail to resynchronize, and the attempts to
# repair them, before the Python loop takes over.
READERS_FAILURES_DIVISOR = 4
READERS_ROUNDS_MAXIMUM = 16
# Steps of the readers between two checks of the time.
READERS_STEPS_CHECK = 1024

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


class ReaderTables:
    """
    From a table of read_huffman_tables, per value of the next 16 bits: the
    length of the code, the size of its additional bits, the bits that the
    whole difference takes (0 for an invalid code) and the difference.
    """
    def __init__(self, table):
        import numpy

        entries = numpy.array(table, dtype=numpy.int32)
        self.lengths = entries & 255
        self.sizes = entries >> 8

        additional = numpy.where(self.sizes < SIZE_MAXIMUM, self.sizes, 0)
        advance = self.lengths + additional
        advance[self.sizes > SIZE_MAXIMUM] = 0
        self.advance = advance.astype(numpy.uint8)

        whole = advance <= 16
        windows = numpy.arange(65536, dtype=numpy.int32)
        values = (windows >> (16 - advance.clip(max=16))) & (
            (1 << additional) - 1
        )
        self.values = _get_differences(sizes=additional, values=values)
        self.values[self.sizes == SIZE_MAXIMUM] = 32768
        self.values[~whole] = DIFFERENCE_LONG


def _get_differences(sizes, values):
    """Below half of its range, the value of the additional bits is negative."""
    import numpy

    return numpy.where(
        values < ((1 << sizes) >> 1), values - ((1 << sizes) - 1), values
    )


def _get_words(data):
    """
    The 24 bits that start at each byte of the data. After the data come zeros,
    as in the Python loop for a last code cut in two.
    """
    import numpy

    values = numpy.frombuffer(data + bytes(8), dtype=numpy.uint8)
    # In place: the data can be large and this is four bytes per byte already.
    words = values[:-2].astype(numpy.uint32)
    words <<= 8
    words |= values[1:-1]
    words <<= 8
    words |= values[2:]
    return words


def _count_with_readers(
    active, advance, counts, deadline, invalid, positions, stops, words
):
    """
    Move the active readers from their position to their stop, or to an invalid
    code, and count the differences they go over.
    """
    current = positions[active]
    stop = stops[active]
    step = 0

    while current.size:
        step += 1
        if not step % READERS_STEPS_CHECK:
            stop_if_late(deadline=deadline)

        jumps = advance[
            (words[current >> 3] >> (8 - (current & 7))) & SAMPLE_MASK
        ]
        current += jumps
        running = current < stop

        if not jumps.all():
            blocked = jumps == 0
            invalid[active[blocked]] = True
            counts[active[blocked]] -= 1
            running &= ~blocked

        if not running.all():
            finished = ~running
            positions[active[finished]] = current[finished]
            counts[active[finished]] += step
            active = active[running]
            current = current[running]
            stop = stop[running]


def _plan_readers(advance, count, deadline, size_bits, words):
    """
    Where each reader starts and the differences it reads, or None when the
    stream is not one that the readers can read.
    """
    import numpy

    spacing = max(READERS_SPACING_MINIMUM, size_bits >> READERS_SPACING_SHIFT)
    seeds = numpy.arange(spacing, size_bits, spacing, dtype=numpy.int64)
    # Not on the right codes yet, a reader can meet invalid ones: one bit further
    # is as good a place as any other.
    for _ in range(READERS_SYNCHRONIZATION):
        seeds = numpy.minimum(
            seeds + numpy.maximum(
                advance[
                    (words[seeds >> 3] >> (8 - (seeds & 7))) & SAMPLE_MASK
                ], 1
            ), size_bits
        )

    # The first bit of the stream is the only place known to be right.
    starts = numpy.unique(
        numpy.concatenate(
            (numpy.zeros(1, dtype=numpy.int64), seeds[seeds < size_bits])
        )
    )
    stops = numpy.append(starts[1:], size_bits)
    positions = starts.copy()
    alive = numpy.ones(starts.size, dtype=bool)
    invalid = numpy.zeros(starts.size, dtype=bool)
    counts = numpy.zeros(starts.size, dtype=numpy.int64)

    for attempt in range(READERS_ROUNDS_MAXIMUM):
        _count_with_readers(
            active=numpy.flatnonzero(alive & ~invalid & (positions < stops)),
            advance=advance, counts=counts, deadline=deadline, invalid=invalid,
            positions=positions, stops=stops, words=words
        )

        # A reader that jumped over the start of the next one: the next one did
        # not resynchronize in time, this one continues up to its stop.
        failed = numpy.flatnonzero(
            alive & (positions > stops) & (stops < size_bits)
        )
        if not failed.size:
            break
        if not attempt and failed.size > starts.size // READERS_FAILURES_DIVISOR:
            return None

        for reader in failed.tolist():
            following = reader + 1
            while alive[reader] and following < starts.size and (
                positions[reader] > stops[reader]
            ):
                if alive[following]:
                    alive[following] = False
                    stops[reader] = stops[following]
                following += 1
    else:
        return None

    readers = numpy.flatnonzero(alive)
    totals = numpy.cumsum(counts[readers])
    needed = int(numpy.searchsorted(totals, count))
    if needed >= readers.size:
        return None

    # Each reader used must have ended exactly where the next one starts.
    used = readers[:needed]
    following = starts[readers[1:needed + 1]]
    if (positions[used] != following).any():
        return None

    readers = readers[:needed + 1]
    counts = counts[readers]
    counts[-1] -= int(totals[needed]) - count
    return starts[readers], counts


def _write_with_readers(counts, deadline, output, starts, tables, words):
    """Write the differences that the readers go over at their place."""
    import numpy

    targets = numpy.cumsum(counts) - counts
    current = starts.copy()
    remaining = counts.copy()
    step = 0
    finish = int(remaining.min())

    while current.size:
        step += 1
        if not step % READERS_STEPS_CHECK:
            stop_if_late(deadline=deadline)

        windows = (words[current >> 3] >> (8 - (current & 7))) & SAMPLE_MASK
        values = tables.values[windows]

        long_values = numpy.flatnonzero(values == DIFFERENCE_LONG)
        if long_values.size:
            found = windows[long_values]
            sizes = tables.sizes[found].astype(numpy.int64)
            at = current[long_values] + tables.lengths[found]
            values[long_values] = _get_differences(
                sizes=sizes, values=(
                    (words[at >> 3] >> (8 - (at & 7))) & SAMPLE_MASK
                ) >> (16 - sizes)
            )

        output[targets] = values
        current += tables.advance[windows]
        targets += 1

        if step == finish:
            running = remaining != step
            current = current[running]
            targets = targets[running]
            remaining = remaining[running]
            if remaining.size:
                finish = int(remaining.min())


def _read_segment_with_readers(count, data, deadline, output, tables):
    """
    Write the differences of a segment in the output. Return False, with the
    output as it was, for the Python loop to read the segment.
    """
    # No difference can start after that, whatever follows in the file.
    size_bits = min(len(data) * 8, count * DIFFERENCE_BITS_MAXIMUM)
    words = _get_words(data=data[:size_bits // 8 + 8])
    plan = _plan_readers(
        advance=tables.advance, count=count, deadline=deadline,
        size_bits=size_bits, words=words
    )
    if plan is None:
        return False

    _write_with_readers(
        counts=plan[1], deadline=deadline, output=output, starts=plan[0],
        tables=tables, words=words
    )
    return True


def _read_differences(
    columns, count, deadline, restart_interval, segments, tables
):
    """
    The differences of a scan, in the order of the file. A restart interval
    is counted in samples here.
    """
    import numpy

    differences = array('i', bytes(4 * count))
    index = 0
    damaged = 0
    decoded = 0
    reader_tables = None
    if count >= READERS_SAMPLES_MINIMUM and all(
        item is tables[0] for item in tables
    ):
        reader_tables = ReaderTables(table=tables[0])
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

        if reader_tables and limit - index >= READERS_SAMPLES_MINIMUM and (
            _read_segment_with_readers(
                count=limit - index, data=data, deadline=deadline,
                output=numpy.frombuffer(
                    differences, dtype=numpy.intc
                )[index:limit], tables=reader_tables
            )
        ):
            decoded += limit - index
            index = limit
            continue

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

    values[1:] += (previous[1:] - previous[:-1]) >> 1
    return numpy.cumsum(values) & SAMPLE_MASK


def _get_samples_by_diagonals(differences, deadline, initial, predictor):
    """The samples of a restart interval, for the predictors 6 and 7."""
    import numpy

    rows, columns = differences.shape
    samples = numpy.empty((rows, columns), dtype=numpy.int32)

    # The first row is predicted from the left, the first column from above.
    values = differences[0].astype(numpy.int64)
    values[0] += initial
    samples[0] = numpy.cumsum(values) & SAMPLE_MASK
    samples[1:, 0] = (
        samples[0, 0] + numpy.cumsum(differences[1:, 0].astype(numpy.int64))
    ) & SAMPLE_MASK

    # In the flat arrays, one row down and one column to the left.
    step = columns - 1
    flat = samples.reshape(-1)
    flat_differences = numpy.asarray(differences).reshape(-1)

    for diagonal in range(2, rows + columns - 1):
        if not diagonal % 256:
            stop_if_late(deadline=deadline)

        first = max(1, diagonal - step)
        last = min(rows - 1, diagonal - 1)
        if first > last:
            continue

        start = first * columns + diagonal - first
        stop = last * columns + diagonal - last + 1
        left = flat[start - 1:stop - 1:step]
        above = flat[start - columns:stop - columns:step]
        if predictor == 6:
            prediction = above + (
                (left - flat[start - columns - 1:stop - columns - 1:step]) >> 1
            )
        else:
            prediction = (left + above) >> 1
        flat[start:stop:step] = (
            flat_differences[start:stop:step] + prediction
        ) & SAMPLE_MASK

    return samples


def _get_plane(differences, deadline, predictor, restart_rows, transform, initial):
    """The samples of a component from its differences."""
    import numpy

    rows, columns = differences.shape
    plane = numpy.empty((rows, columns), dtype=numpy.uint16)
    previous = None

    if predictor > 5:
        for row in range(0, rows, restart_rows or rows):
            part = differences[row:row + (restart_rows or rows)]
            plane[row:row + part.shape[0]] = (
                _get_samples_by_diagonals(
                    deadline=deadline, differences=part, initial=initial,
                    predictor=predictor
                ) << transform
            ) & SAMPLE_MASK
        return plane

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
