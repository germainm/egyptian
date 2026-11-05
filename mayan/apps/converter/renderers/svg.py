"""
Drawings of the SVG files, by rsvg-convert, the command line program of librsvg
(LGPL-2.1 or later), started for each drawing. CairoSVG (LGPL-3.0 or later) did
this before, inside the process of this project.

The data comes from outside. Reading from its standard input, rsvg-convert has
no base address: it loads nothing from the network or from the disk, and refuses
external XML entities. A few bytes can still ask for a huge drawing, so memory
and time are limited.
"""
import base64
import shutil
import subprocess
from urllib.parse import unquote_to_bytes

from ..literals import DEFAULT_RSVG_CONVERT_PATH
from ..settings import setting_graphics_backend_arguments

# Four bytes per pixel: a drawing above about 390 megapixels is refused at once.
# Pillow refuses the image above 179 by default, once it is drawn. A small drawing
# fits in 64 MB.
MEMORY_MAXIMUM = 1536 * 1024 * 1024
TIME_MAXIMUM = 60

DATA_URL_PREFIX = 'data:image/svg+xml'
DATA_URL_BASE64_SUFFIX = ';base64'


class SVGRenderError(ValueError):
    """The drawing cannot be rendered."""


def get_rsvg_convert_path():
    return setting_graphics_backend_arguments.value.get(
        'rsvg_convert_path', DEFAULT_RSVG_CONVERT_PATH
    )


def get_command():
    command = [get_rsvg_convert_path(), '--format=png']
    prlimit_path = shutil.which('prlimit')
    if prlimit_path:
        command[:0] = [
            prlimit_path, '--as={}'.format(MEMORY_MAXIMUM), '--'
        ]
    return command


def render_svg(data):
    """Return the drawing as an image of the size that the file declares."""
    import io

    from PIL import Image

    try:
        process = subprocess.run(
            args=get_command(), capture_output=True, input=data,
            timeout=TIME_MAXIMUM
        )
    except FileNotFoundError as exception:
        raise SVGRenderError(
            'rsvg-convert not installed or not found.'
        ) from exception
    except subprocess.TimeoutExpired as exception:
        raise SVGRenderError(
            'Drawing not rendered after {} seconds.'.format(TIME_MAXIMUM)
        ) from exception

    if process.returncode:
        raise SVGRenderError(
            'Drawing not rendered; {}'.format(
                process.stderr.decode(errors='replace').strip()[:300] or (
                    'exit code {}'.format(process.returncode)
                )
            )
        )

    return Image.open(fp=io.BytesIO(initial_bytes=process.stdout))


def render_svg_data_url(url):
    """
    The image of a drawing given as a data: URL, the only kind of address that
    is read: this one comes from outside too, and could name anything else.
    """
    header, separator, content = url.partition(',')
    header = header.strip().lower()
    if not separator or not header.startswith(DATA_URL_PREFIX):
        raise SVGRenderError('Not the data: URL of an SVG drawing.')

    if header.endswith(DATA_URL_BASE64_SUFFIX):
        try:
            data = base64.b64decode(content)
        except ValueError as exception:
            raise SVGRenderError('Invalid data: URL.') from exception
    else:
        data = unquote_to_bytes(content)

    return render_svg(data=data)
