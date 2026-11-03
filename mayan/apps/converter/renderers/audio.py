"""
Page of an audio file: its tags (title, artist, album…), its cover when the
file holds one, its waveform and its technical properties. Read with ffprobe
and drawn with ffmpeg and Pillow.
"""
import io
import json
import logging

from PIL import Image

from . import (
    PAGE_ACCENT, PAGE_INK_MUTED, PAGE_MARGIN, PAGE_RULE,
    clean_text, draw_fields, draw_lines, format_duration, get_font,
    new_page, wrap_text
)

logger = logging.getLogger(name=__name__)

PAGE_WIDTH = 1600
PAGE_HEIGHT = 1200
COVER_SIZE = 520
WAVEFORM_HEIGHT = 240

# Tags shown first, in this order, with their label; the other tags follow.
AUDIO_TAGS = (
    ('album_artist', 'Album artist'),
    ('album', 'Album'),
    ('date', 'Date'),
    ('year', 'Year'),
    ('track', 'Track'),
    ('disc', 'Disc'),
    ('genre', 'Genre'),
    ('composer', 'Composer'),
    ('performer', 'Performer'),
    ('conductor', 'Conductor'),
    ('publisher', 'Publisher'),
    ('copyright', 'Copyright'),
    ('language', 'Language'),
    ('comment', 'Comment'),
    ('description', 'Description'),
)
# Tags that carry no information for a reader.
AUDIO_TAGS_HIDDEN = {
    'encoder', 'encoded_by', 'major_brand', 'minor_version',
    'compatible_brands', 'handler_name', 'vendor_id', 'title', 'artist',
    'itunsmpb', 'itunnorm', 'creation_time', 'lyrics',
}
AUDIO_TAGS_OTHER_MAXIMUM = 6


def get_audio_information(command_ffprobe, path, timeout):
    output = command_ffprobe(
        '-v', 'error', '-show_format', '-show_streams', '-of', 'json', path,
        _timeout=timeout
    )
    return json.loads(str(output))


def get_tags(information):
    """Tags of the file and of its audio stream (Ogg files keep them there)."""
    tags = {}
    sources = [information.get('format', {})]
    sources.extend(
        stream for stream in information.get('streams', [])
        if stream.get('codec_type') == 'audio'
    )
    for source in sources:
        for key, value in (source.get('tags') or {}).items():
            key = key.lower().replace(' ', '_')
            if value and str(value).strip() and key not in tags:
                tags[key] = str(value).strip()
    return tags


def get_cover(command_ffmpeg, path, information, timeout):
    """The picture attached to the file (ID3 APIC, FLAC PICTURE, MP4 covr)."""
    for stream in information.get('streams', []):
        if stream.get('codec_type') != 'video':
            continue
        try:
            output = io.BytesIO()
            command_ffmpeg(
                '-nostdin', '-v', 'error', '-i', path,
                '-map', '0:{}'.format(stream['index']), '-frames:v', '1',
                '-f', 'image2pipe', '-vcodec', 'png', '-',
                _out=output, _timeout=timeout
            )
            output.seek(0)
            cover = Image.open(fp=output)
            cover.load()
            return cover.convert(mode='RGB')
        except Exception as exception:
            logger.debug('Cover of the audio file not read; %s', exception)
    return None


def get_waveform(command_ffmpeg, path, width, height, timeout):
    output = io.BytesIO()
    command_ffmpeg(
        '-nostdin', '-v', 'error', '-i', path, '-filter_complex',
        # Square root scale: quiet recordings stay visible.
        'aformat=channel_layouts=mono,showwavespic=s={}x{}:scale=sqrt:colors=0x{:02x}{:02x}{:02x}'.format(
            width, height, *PAGE_ACCENT
        ),
        '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-',
        _out=output, _timeout=timeout
    )
    output.seek(0)
    waveform = Image.open(fp=output)
    waveform.load()
    return waveform.convert(mode='RGBA')


def get_technical_fields(information):
    audio = next(
        (
            stream for stream in information.get('streams', [])
            if stream.get('codec_type') == 'audio'
        ), {}
    )
    file_format = information.get('format', {})
    fields = []
    duration = file_format.get('duration') or audio.get('duration')
    if duration:
        fields.append(('Duration', format_duration(float(duration))))
    codec = audio.get('codec_long_name') or audio.get('codec_name')
    if codec:
        fields.append(('Encoding', codec))
    bit_rate = audio.get('bit_rate') or file_format.get('bit_rate')
    if bit_rate:
        fields.append(('Bit rate', '{} kbit/s'.format(int(bit_rate) // 1000)))
    if audio.get('sample_rate'):
        fields.append(
            ('Sampling', '{:g} kHz'.format(int(audio['sample_rate']) / 1000))
        )
    channels = audio.get('channel_layout') or {1: 'mono', 2: 'stereo'}.get(
        audio.get('channels'), audio.get('channels')
    )
    if channels:
        fields.append(('Channels', str(channels)))
    if file_format.get('format_long_name'):
        fields.append(('Container', file_format['format_long_name']))
    return fields, float(duration or 0)


def render_audio_page(command_ffmpeg, command_ffprobe, path, timeout):
    information = get_audio_information(
        command_ffprobe=command_ffprobe, path=path, timeout=timeout
    )
    if not any(
        stream.get('codec_type') == 'audio'
        for stream in information.get('streams', [])
    ):
        raise ValueError('The file has no audio stream.')

    tags = get_tags(information=information)
    image, draw = new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    content_width = PAGE_WIDTH - 2 * PAGE_MARGIN

    # Title and artist.
    title = tags.get('title') or clean_text(
        information.get('format', {}).get('filename', '').rsplit('/', 1)[-1]
    ) or 'Audio file'
    font_title = get_font(size=58, style='bold')
    y = draw_lines(
        draw=draw, xy=(PAGE_MARGIN, PAGE_MARGIN),
        lines=wrap_text(
            draw=draw, text=clean_text(title), font=font_title,
            width=content_width, maximum_lines=2
        ), font=font_title, spacing=1.15
    )
    if tags.get('artist'):
        font_artist = get_font(size=40)
        y = draw_lines(
            draw=draw, xy=(PAGE_MARGIN, y + 4),
            lines=wrap_text(
                draw=draw, text=clean_text(tags['artist']), font=font_artist,
                width=content_width, maximum_lines=1
            ), font=font_artist, fill=PAGE_INK_MUTED
        )
    y += 24
    draw.line(
        xy=((PAGE_MARGIN, y), (PAGE_WIDTH - PAGE_MARGIN, y)),
        fill=PAGE_RULE, width=3
    )
    y += 36

    # Cover, or a frame with a note when the file has none.
    cover = get_cover(
        command_ffmpeg=command_ffmpeg, path=path, information=information,
        timeout=timeout
    )
    box = (PAGE_MARGIN, y, PAGE_MARGIN + COVER_SIZE, y + COVER_SIZE)
    if cover:
        cover.thumbnail(size=(COVER_SIZE, COVER_SIZE))
        image.paste(
            im=cover, box=(
                box[0] + (COVER_SIZE - cover.width) // 2,
                box[1] + (COVER_SIZE - cover.height) // 2
            )
        )
    else:
        draw.rectangle(xy=box, outline=PAGE_RULE, width=3)
        font_note = get_font(size=200)
        note = '♪'
        draw.text(
            xy=(
                box[0] + (COVER_SIZE - draw.textlength(note, font=font_note)) / 2,
                box[1] + COVER_SIZE / 2 - 130
            ), text=note, font=font_note, fill=PAGE_RULE
        )

    # Tags and technical properties, right of the cover.
    fields = []
    shown = set()
    for key, label in AUDIO_TAGS:
        if key in tags and not (key == 'year' and 'date' in tags):
            fields.append((label, tags[key]))
            shown.add(key)
    others = [
        (key.replace('_', ' ').capitalize(), value)
        for key, value in sorted(tags.items())
        if key not in shown and key not in AUDIO_TAGS_HIDDEN
    ]
    fields.extend(others[:AUDIO_TAGS_OTHER_MAXIMUM])
    technical_fields, duration = get_technical_fields(information=information)
    x = PAGE_MARGIN + COVER_SIZE + 50
    y_fields = draw_fields(
        draw=draw, xy=(x, y), fields=fields + technical_fields,
        width=PAGE_WIDTH - PAGE_MARGIN - x, size=28
    )

    # Waveform across the page, with the time at both ends.
    y = max(y + COVER_SIZE, y_fields) + 40
    try:
        waveform = get_waveform(
            command_ffmpeg=command_ffmpeg, path=path, width=content_width,
            height=WAVEFORM_HEIGHT, timeout=timeout
        )
    except Exception as exception:
        logger.debug('Waveform of the audio file not drawn; %s', exception)
    else:
        if y + WAVEFORM_HEIGHT + 60 > PAGE_HEIGHT:
            y = PAGE_HEIGHT - WAVEFORM_HEIGHT - 60
        draw.line(
            xy=(
                (PAGE_MARGIN, y + WAVEFORM_HEIGHT // 2),
                (PAGE_WIDTH - PAGE_MARGIN, y + WAVEFORM_HEIGHT // 2)
            ), fill=PAGE_RULE, width=1
        )
        image.paste(im=waveform, box=(PAGE_MARGIN, y), mask=waveform)
        font_time = get_font(size=24, style='mono')
        y += WAVEFORM_HEIGHT + 8
        draw.text(
            xy=(PAGE_MARGIN, y), text='0:00', font=font_time,
            fill=PAGE_INK_MUTED
        )
        end = format_duration(duration)
        draw.text(
            xy=(
                PAGE_WIDTH - PAGE_MARGIN - draw.textlength(end, font=font_time), y
            ), text=end, font=font_time, fill=PAGE_INK_MUTED
        )

    del draw
    return image

