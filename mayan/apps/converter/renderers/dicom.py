"""
Pages of a DICOM file.

- Images: one page per frame, shown as the file asks: modality LUT (rescale
  slope and intercept), then the window or VOI LUT of the file (top level or
  functional groups of the enhanced multi-frame images), palette colors,
  MONOCHROME1 inverted.
- Objects without image (structured reports, ECG, radiotherapy plans) and
  images that no installed decoder can read: pages of the main attributes,
  with the content of the structured report and the leads of the ECG.
"""
from collections.abc import Sequence
import logging
import math

from PIL import Image, ImageDraw

from . import (
    PAGE_ACCENT, PAGE_INK, PAGE_INK_MUTED, PAGE_MARGIN, PAGE_RULE,
    clean_text, draw_fields, get_font, new_page, wrap_text
)

logger = logging.getLogger(name=__name__)

PAGE_WIDTH = 1600
PAGE_HEIGHT = 2000
TEXT_SIZE = 28
NOTE_COLOR = (179, 38, 30)
ECG_HEIGHT = 1150
ECG_GRID = (246, 205, 210)
ECG_TRACE = (26, 31, 46)
SR_DEPTH_MAXIMUM = 12
SR_LINES_MAXIMUM = 2000
DECODER_HINTS = (
    'install python-gdcm, or pylibjpeg with pylibjpeg-libjpeg (JPEG '
    'lossless, JPEG-LS, 12-bit JPEG) and pylibjpeg-openjpeg (JPEG 2000)'
)

SUMMARY_ATTRIBUTES = (
    ('PatientName', 'Patient'),
    ('PatientID', 'Patient ID'),
    ('PatientBirthDate', 'Birth date'),
    ('PatientSex', 'Sex'),
    ('StudyDate', 'Study date'),
    ('StudyDescription', 'Study'),
    ('SeriesDescription', 'Series'),
    ('AccessionNumber', 'Accession number'),
    ('Modality', 'Modality'),
    ('BodyPartExamined', 'Body part'),
    ('InstitutionName', 'Institution'),
    ('ReferringPhysicianName', 'Referring physician'),
    ('Manufacturer', 'Manufacturer'),
    ('ManufacturerModelName', 'Model'),
    ('ContentDate', 'Content date'),
)


def _read(file_object):
    import pydicom

    file_object.seek(0)
    try:
        # Large values (the pixel data) are read only when used.
        return pydicom.dcmread(file_object, force=True, defer_size=256 * 1024)
    finally:
        file_object.seek(0)


def _has_pixels(dataset):
    return any(
        keyword in dataset
        for keyword in ('PixelData', 'FloatPixelData', 'DoubleFloatPixelData')
    )


def _frame_count(dataset):
    try:
        return max(1, int(dataset.get('NumberOfFrames', 1) or 1))
    except (TypeError, ValueError):
        return 1


def _transfer_syntax(dataset):
    from pydicom.uid import ImplicitVRLittleEndian

    return getattr(
        getattr(dataset, 'file_meta', None), 'TransferSyntaxUID', None
    ) or ImplicitVRLittleEndian


def _decoder_problem(dataset):
    """Why the pixel data cannot be decoded, or None."""
    from pydicom.pixels import get_decoder

    transfer_syntax = _transfer_syntax(dataset)
    if not transfer_syntax.is_compressed:
        return None
    try:
        decoder = get_decoder(transfer_syntax)
    except NotImplementedError:
        return 'no decoder exists for {} in pydicom'.format(transfer_syntax.name)
    if not decoder.is_available:
        return 'no decoder installed for {}: {}'.format(
            transfer_syntax.name, DECODER_HINTS
        )
    return None


def _decode_frame(file_object, dataset, index):
    from pydicom.pixels import pixel_array

    file_object.seek(0)
    try:
        return pixel_array(file_object, index=index)
    except (AttributeError, NotImplementedError, ValueError):
        # Deflated datasets and files that the frame reader does not
        # handle: decode the whole pixel data of the dataset.
        array = dataset.pixel_array
        if _frame_count(dataset) > 1:
            array = array[index]
        return array
    finally:
        file_object.seek(0)


def _frame_value(dataset, index, sequence, keyword):
    """
    An attribute of the frame: top level, else functional groups of the
    frame, else shared functional groups (enhanced multi-frame images).
    """
    if keyword in dataset:
        return dataset[keyword].value
    for groups_keyword, item_index in (
        ('PerFrameFunctionalGroupsSequence', index),
        ('SharedFunctionalGroupsSequence', 0)
    ):
        groups = dataset.get(groups_keyword)
        try:
            item = groups[item_index][sequence][0]
        except (IndexError, KeyError, TypeError):
            continue
        if keyword in item:
            return item[keyword].value
    return None


def _first(value):
    """First value of a multi-valued attribute (window center, width)."""
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        value = value[0] if len(value) else None
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _to_8_bits(array, low=None, high=None):
    import numpy

    array = array.astype('float64')
    if low is None or high is None or high <= low:
        finite = array[numpy.isfinite(array)]
        if not finite.size:
            return numpy.zeros(array.shape, dtype='uint8')
        low, high = float(finite.min()), float(finite.max())
    if high <= low:
        return numpy.zeros(array.shape, dtype='uint8')
    array = numpy.nan_to_num((array - low) / (high - low), nan=0.0)
    return (numpy.clip(array, 0, 1) * 255).round().astype('uint8')


def _frame_image(dataset, array, index):
    from pydicom.pixels import apply_color_lut, apply_voi_lut

    photometric = str(dataset.get('PhotometricInterpretation', 'MONOCHROME2'))

    if photometric == 'PALETTE COLOR':
        array = apply_color_lut(array, dataset)
        maximum = 255 if array.max() <= 255 else 65535
        return Image.fromarray(_to_8_bits(array, 0, maximum))

    if array.ndim == 3:
        # RGB; pydicom converts the YBR color spaces to RGB.
        maximum = float(2 ** int(dataset.get('BitsStored', 8) or 8) - 1)
        if array.shape[2] == 4:
            array = array[:, :, :3]
        return Image.fromarray(_to_8_bits(array, 0, maximum))

    slope = _first(_frame_value(dataset, index, 'PixelValueTransformationSequence', 'RescaleSlope'))
    intercept = _first(_frame_value(dataset, index, 'PixelValueTransformationSequence', 'RescaleIntercept'))
    if 'ModalityLUTSequence' in dataset:
        # The LUT is indexed by the stored (integer) values.
        from pydicom.pixels import apply_modality_lut
        array = apply_modality_lut(array, dataset).astype('float64')
    else:
        array = array.astype('float64')
        if slope is not None or intercept is not None:
            array = array * (slope if slope is not None else 1) + (intercept or 0)

    center = _first(_frame_value(dataset, index, 'FrameVOILUTSequence', 'WindowCenter'))
    width = _first(_frame_value(dataset, index, 'FrameVOILUTSequence', 'WindowWidth'))
    if 'VOILUTSequence' in dataset and center is None:
        image = _to_8_bits(apply_voi_lut(array, dataset, index=0))
    elif center is not None and width and width > 0:
        image = _to_8_bits(array, center - width / 2, center + width / 2)
    else:
        image = _to_8_bits(array)

    if photometric == 'MONOCHROME1':
        image = 255 - image
    return Image.fromarray(image)


def _format_value(keyword, value):
    text = str(value)
    if keyword.endswith('Date') and len(text) == 8 and text.isdigit():
        return '{}-{}-{}'.format(text[:4], text[4:6], text[6:])
    if keyword.endswith('Name'):
        return text.replace('^', ' ').strip()
    return text


def _summary_fields(dataset):
    fields = []
    for keyword, label in SUMMARY_ATTRIBUTES:
        value = dataset.get(keyword)
        if value is None or str(value).strip() == '':
            continue
        text = _format_value(keyword=keyword, value=value)
        if keyword == 'StudyDate' and dataset.get('StudyTime'):
            time = str(dataset.StudyTime)
            if len(time) >= 4 and time[:4].isdigit():
                text = '{} {}:{}'.format(text, time[:2], time[2:4])
        fields.append((label, text))
    return fields


def _code_meaning(item, keyword):
    try:
        return str(item[keyword][0].CodeMeaning)
    except (AttributeError, IndexError, KeyError, TypeError):
        return ''


def _content_lines(dataset):
    """Lines (depth, text, is_heading) of the content of a structured report."""
    lines = []

    def walk(items, depth):
        for item in items:
            if len(lines) >= SR_LINES_MAXIMUM:
                return
            concept = _code_meaning(item, 'ConceptNameCodeSequence')
            value_type = str(item.get('ValueType', ''))
            value = ''
            if value_type == 'TEXT':
                value = str(item.get('TextValue', ''))
            elif value_type == 'CODE':
                value = _code_meaning(item, 'ConceptCodeSequence')
            elif value_type == 'NUM':
                try:
                    measure = item.MeasuredValueSequence[0]
                    value = '{} {}'.format(
                        measure.NumericValue,
                        measure.MeasurementUnitsCodeSequence[0].CodeValue
                    )
                except (AttributeError, IndexError):
                    value = ''
            elif value_type == 'PNAME':
                value = str(item.get('PersonName', '')).replace('^', ' ')
            elif value_type in ('DATE', 'TIME', 'DATETIME'):
                value = str(
                    item.get('Date') or item.get('Time') or item.get('DateTime') or ''
                )
            elif value_type == 'UIDREF':
                value = str(item.get('UID', ''))
            if value_type == 'CONTAINER':
                if concept:
                    lines.append((depth, concept, True))
            elif concept or value:
                text = '{}: {}'.format(concept, value) if concept and value else concept or value
                for paragraph in str(text).splitlines() or ['']:
                    lines.append((depth, paragraph, False))
            if 'ContentSequence' in item and depth < SR_DEPTH_MAXIMUM:
                walk(item.ContentSequence, depth + 1)

    if 'ContentSequence' in dataset:
        walk(dataset.ContentSequence, 0)
    return lines


def _title(dataset):
    try:
        name = dataset.SOPClassUID.name
    except AttributeError:
        name = ''
    return clean_text(name or 'DICOM {}'.format(dataset.get('Modality', 'object')))


class SummaryLayout:
    """Pages of the attributes and report content, laid out once."""

    def __init__(self, dataset, note=None):
        self.dataset = dataset
        self.note = note
        self.has_ecg = 'WaveformSequence' in dataset
        image, draw = new_page(width=10, height=10)
        self.draw = draw
        self.font = get_font(size=TEXT_SIZE)
        self.font_heading = get_font(size=TEXT_SIZE, style='bold')
        self.line_height = int(TEXT_SIZE * 1.35)
        self.content_width = PAGE_WIDTH - 2 * PAGE_MARGIN
        self.header_height = self._draw_header(draw=draw)
        # Lines of the report, wrapped to the width of the page.
        self.lines = []
        for depth, text, is_heading in _content_lines(dataset):
            indent = min(depth, 8) * 36
            font = self.font_heading if is_heading else self.font
            for line in wrap_text(
                draw=draw, text=clean_text(text, maximum_length=4000), font=font,
                width=self.content_width - indent
            ):
                self.lines.append((indent, line, is_heading))
        first_page_space = PAGE_HEIGHT - PAGE_MARGIN - self.header_height - (
            ECG_HEIGHT if self.has_ecg else 0
        )
        self.first_page_lines = max(0, first_page_space // self.line_height)
        self.other_page_lines = (PAGE_HEIGHT - 2 * PAGE_MARGIN) // self.line_height
        remaining = max(0, len(self.lines) - self.first_page_lines)
        self.page_count = 1 + math.ceil(remaining / self.other_page_lines)

    def _draw_header(self, draw):
        y = PAGE_MARGIN
        font_title = get_font(size=46, style='bold')
        for line in wrap_text(
            draw=draw, text=_title(self.dataset), font=font_title,
            width=self.content_width, maximum_lines=2
        ):
            draw.text(xy=(PAGE_MARGIN, y), text=line, font=font_title, fill=PAGE_INK)
            y += 58
        y += 10
        if self.note:
            font_note = get_font(size=TEXT_SIZE, style='bold')
            for line in wrap_text(
                draw=draw, text=self.note, font=font_note,
                width=self.content_width, maximum_lines=4
            ):
                draw.text(xy=(PAGE_MARGIN, y), text=line, font=font_note, fill=NOTE_COLOR)
                y += self.line_height
            y += 10
        y = draw_fields(
            draw=draw, xy=(PAGE_MARGIN, y), fields=_summary_fields(self.dataset),
            width=self.content_width, size=TEXT_SIZE
        )
        draw.line(
            xy=((PAGE_MARGIN, y + 6), (PAGE_WIDTH - PAGE_MARGIN, y + 6)),
            fill=PAGE_RULE, width=3
        )
        return y + 30

    def render(self, page_number):
        image, draw = new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        if page_number == 0:
            y = self._draw_header(draw=draw)
            if self.has_ecg:
                try:
                    _draw_ecg(
                        image=image, dataset=self.dataset,
                        box=(PAGE_MARGIN, y, PAGE_WIDTH - PAGE_MARGIN, y + ECG_HEIGHT - 40)
                    )
                except Exception as exception:
                    logger.warning('ECG leads not drawn; %s', exception)
                y += ECG_HEIGHT
            lines = self.lines[:self.first_page_lines]
        else:
            y = PAGE_MARGIN
            start = self.first_page_lines + (page_number - 1) * self.other_page_lines
            lines = self.lines[start:start + self.other_page_lines]
        for indent, line, is_heading in lines:
            draw.text(
                xy=(PAGE_MARGIN + indent, y), text=line,
                font=self.font_heading if is_heading else self.font,
                fill=PAGE_ACCENT if is_heading else PAGE_INK
            )
            y += self.line_height
        del draw
        return image


def _draw_ecg(image, dataset, box):
    """The channels of the first waveform group, one strip each."""
    import numpy

    group = dataset.WaveformSequence[0]
    samples = dataset.waveform_array(0)
    if samples.ndim == 1:
        samples = samples[:, None]
    frequency = float(group.get('SamplingFrequency', 0) or 0)
    left, top, right, bottom = box
    channel_count = min(samples.shape[1], 16)
    strip = (bottom - top) / channel_count
    draw = ImageDraw.Draw(image)
    label_width = 130
    plot_left = left + label_width
    width = right - plot_left
    duration = samples.shape[0] / frequency if frequency else None

    # Grid every 0.2 s, as on ECG paper.
    if duration:
        step = width / (duration / 0.2)
        x = plot_left
        while x <= right:
            draw.line(xy=((x, top), (x, bottom)), fill=ECG_GRID, width=1)
            x += step
    font = get_font(size=22, style='bold')
    definitions = group.get('ChannelDefinitionSequence', [])
    for channel in range(channel_count):
        values = samples[:, channel].astype('float64')
        values = values[numpy.isfinite(values)] if values.size else values
        center = top + strip * (channel + 0.5)
        try:
            label = definitions[channel].ChannelSourceSequence[0].CodeMeaning
        except (AttributeError, IndexError, KeyError):
            label = 'Channel {}'.format(channel + 1)
        # "Lead I (Einthoven)" → "I".
        label = clean_text(
            str(label).split(' (')[0].replace('Lead ', ''), maximum_length=10
        )
        draw.text(xy=(left, center - 12), text=label, font=font, fill=PAGE_INK_MUTED)
        if not values.size:
            continue
        span = float(numpy.percentile(numpy.abs(values - numpy.median(values)), 99.5)) or 1.0
        scale = (strip * 0.45) / span
        median = float(numpy.median(values))
        step = max(1, int(len(values) / (width * 2)))
        reduced = values[::step]
        points = [
            (plot_left + width * position / max(1, len(reduced) - 1), center - (value - median) * scale)
            for position, value in enumerate(reduced)
        ]
        draw.line(xy=points, fill=ECG_TRACE, width=2)
    if duration:
        draw.text(
            xy=(right - 260, bottom + 6),
            text='{:.1f} s · {:g} Hz'.format(duration, frequency),
            font=get_font(size=22), fill=PAGE_INK_MUTED
        )


def _plan(file_object):
    """Dataset, page count and kind of pages (frames or summary)."""
    dataset = _read(file_object=file_object)
    if not _has_pixels(dataset):
        layout = SummaryLayout(dataset=dataset)
        return dataset, layout.page_count, layout
    problem = _decoder_problem(dataset)
    if problem is None:
        return dataset, _frame_count(dataset), None
    layout = SummaryLayout(
        dataset=dataset, note='Image not decoded: {}.'.format(problem)
    )
    return dataset, layout.page_count, layout


def get_dicom_page_count(file_object):
    dataset, page_count, layout = _plan(file_object=file_object)
    if layout is None and _transfer_syntax(dataset).is_compressed:
        # An available decoder can still fail on the file (12-bit JPEG with
        # Pillow): a single page then explains why.
        try:
            _decode_frame(file_object=file_object, dataset=dataset, index=0)
        except Exception:
            return 1
    return page_count


def render_dicom_page(file_object, page_number):
    dataset, page_count, layout = _plan(file_object=file_object)
    if layout is not None:
        return layout.render(page_number=min(page_number, page_count - 1))
    index = min(page_number, page_count - 1)
    try:
        array = _decode_frame(file_object=file_object, dataset=dataset, index=index)
    except Exception as exception:
        # pydicom names the plugins on the following lines: keep them.
        lines = [line.strip() for line in str(exception).splitlines() if line.strip()]
        message = ' '.join(lines[:3]) or type(exception).__name__
        layout = SummaryLayout(
            dataset=dataset, note='Image not decoded: {} ({}).'.format(
                clean_text(message, maximum_length=200), DECODER_HINTS
            )
        )
        return layout.render(page_number=0)
    return _frame_image(dataset=dataset, array=array, index=index)
