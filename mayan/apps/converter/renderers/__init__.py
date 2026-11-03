"""
Page renderers for the formats that have no page of their own: audio files,
GPS tracks, DICOM objects without image. Each one draws a page with Pillow:
the information it shows is then read by the OCR and found by the search.
"""
import logging

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(name=__name__)

PAGE_BACKGROUND = (255, 255, 255)
PAGE_INK = (26, 31, 46)
PAGE_INK_MUTED = (91, 99, 120)
PAGE_ACCENT = (29, 63, 168)
PAGE_RULE = (221, 225, 234)
PAGE_MARGIN = 60

FONT_FILES = {
    'regular': ('DejaVuSans.ttf', 'LiberationSans-Regular.ttf'),
    'bold': ('DejaVuSans-Bold.ttf', 'LiberationSans-Bold.ttf'),
    'mono': ('DejaVuSansMono.ttf', 'LiberationMono-Regular.ttf'),
}

_fonts = {}


def get_font(size, style='regular'):
    key = (size, style)
    if key not in _fonts:
        for filename in FONT_FILES[style]:
            try:
                _fonts[key] = ImageFont.truetype(font=filename, size=size)
                break
            except OSError:
                continue
        else:
            logger.warning(
                'No TrueType font found for the page renderers (%s); '
                'install fonts-dejavu-core.', ', '.join(FONT_FILES[style])
            )
            _fonts[key] = ImageFont.load_default(size=size)
    return _fonts[key]


def clean_text(value, maximum_length=500):
    """One line of printable text, at most maximum_length characters."""
    text = ' '.join(str(value).split())
    text = ''.join(character for character in text if character.isprintable())
    if len(text) > maximum_length:
        text = text[:maximum_length - 1] + '…'
    return text


def wrap_text(draw, text, font, width, maximum_lines=None):
    """Split text in lines no wider than width pixels."""
    lines = []
    for paragraph in str(text).splitlines() or ['']:
        words = paragraph.split(' ')
        line = ''
        for word in words:
            candidate = '{} {}'.format(line, word) if line else word
            if draw.textlength(candidate, font=font) <= width:
                line = candidate
                continue
            if line:
                lines.append(line)
            # A word wider than the line is cut.
            while draw.textlength(word, font=font) > width and len(word) > 1:
                cut = len(word)
                while cut > 1 and draw.textlength(word[:cut], font=font) > width:
                    cut -= 1
                lines.append(word[:cut])
                word = word[cut:]
            line = word
        lines.append(line)
    if maximum_lines and len(lines) > maximum_lines:
        lines = lines[:maximum_lines]
        lines[-1] = lines[-1][:max(1, len(lines[-1]) - 1)] + '…'
    return lines


def draw_lines(draw, xy, lines, font, fill=PAGE_INK, spacing=1.3):
    """Draw lines of text from xy; return the y below the last one."""
    x, y = xy
    line_height = int(font.size * spacing)
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


def draw_fields(draw, xy, fields, width, size=30, label_width=None):
    """
    Draw (label, value) pairs as a two-column table; return the y below it.
    Values are wrapped to the remaining width.
    """
    x, y = xy
    font_label = get_font(size=size, style='bold')
    font_value = get_font(size=size)
    if label_width is None:
        label_width = max(
            [draw.textlength(label, font=font_label) for label, _ in fields] or [0]
        ) + size
    for label, value in fields:
        draw.text((x, y), label, font=font_label, fill=PAGE_INK_MUTED)
        lines = wrap_text(
            draw=draw, text=clean_text(value), font=font_value,
            width=width - label_width, maximum_lines=3
        )
        y = draw_lines(
            draw=draw, xy=(x + label_width, y), lines=lines, font=font_value
        )
        y += int(size * 0.35)
    return y


def new_page(width, height):
    image = Image.new(mode='RGB', size=(width, height), color=PAGE_BACKGROUND)
    return image, ImageDraw.Draw(image)


def format_duration_words(seconds):
    """Duration that cannot be read as a time of day: 1 h 59 min, 18 min."""
    seconds = int(round(seconds or 0))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return '{} h {:02d} min'.format(hours, minutes)
    if minutes:
        return '{} min'.format(minutes)
    return '{} s'.format(seconds)


def format_duration(seconds):
    seconds = int(round(seconds or 0))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return '{}:{:02d}:{:02d}'.format(hours, minutes, seconds)
    return '{}:{:02d}'.format(minutes, seconds)
