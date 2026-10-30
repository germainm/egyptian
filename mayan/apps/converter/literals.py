import os
import platform

from django.conf import settings

CONVERTER_SVG_MIME_TYPE = 'image/svg+xml'

CONVERTER_VIDEO_MIME_TYPES = (
    'video/mp4',
    'video/x-matroska',
    'video/x-msvideo',
    'video/quicktime',
    'video/webm',
    'video/ogg',
    'video/3gpp',
)

CONVERTER_RAW_PHOTO_MIME_TYPES = (
    'image/x-canon-cr2',
    'image/x-canon-crw',
    'image/x-nikon-nef',
    'image/x-sony-arw',
    'image/x-adobe-dng',
    'image/x-olympus-orf',
    'image/x-fuji-raf',
    'image/x-panasonic-rw2',
    'image/x-sigma-x3f',
    'image/x-pentax-pef',
)

CONVERTER_DJVU_MIME_TYPES = (
    'image/vnd.djvu',
    'image/x-djvu',
)

CONVERTER_EML_MIME_TYPE = 'message/rfc822'

CONVERTER_MARKDOWN_MIME_TYPES = (
    'text/markdown',
    'text/x-markdown',
)

CONVERTER_DXF_MIME_TYPES = (
    'image/vnd.dxf',
    'application/dxf',
    'application/x-autocad',
    'application/x-dxf',
)

CONVERTER_STL_MIME_TYPES = (
    'model/stl',
    'model/x.stl-ascii',
    'model/x.stl-binary',
    'application/sla',
)

CONVERTER_EPUB_MIME_TYPE = 'application/epub+zip'

CONVERTER_DICOM_MIME_TYPES = (
    'application/dicom',
    'application/x-dicom',
)

DEFAULT_DJVU_PATH = '/usr/bin/ddjvu'
DEFAULT_DJVUSED_PATH = '/usr/bin/djvused'
DEFAULT_EBOOK_CONVERT_PATH = '/usr/bin/ebook-convert'
DEFAULT_FFMPEG_PATH = '/usr/bin/ffmpeg'
DEFAULT_FFPROBE_PATH = '/usr/bin/ffprobe'

CONVERTER_OFFICE_FILE_MIMETYPES = (
    'application/msword',
    'application/mswrite',
    'application/mspowerpoint',
    'application/msexcel',
    'application/pgp-keys',
    'application/vnd.ms-excel',
    'application/vnd.ms-excel.addin.macroEnabled.12',
    'application/vnd.ms-excel.sheet.binary.macroEnabled.12',
    'application/vnd.ms-powerpoint',
    'application/vnd.oasis.opendocument.chart',
    'application/vnd.oasis.opendocument.chart-template',
    'application/vnd.oasis.opendocument.formula',
    'application/vnd.oasis.opendocument.formula-template',
    'application/vnd.oasis.opendocument.graphics',
    'application/vnd.oasis.opendocument.graphics-template',
    'application/vnd.oasis.opendocument.image',
    'application/vnd.oasis.opendocument.image-template',
    'application/vnd.oasis.opendocument.presentation',
    'application/vnd.oasis.opendocument.presentation-template',
    'application/vnd.oasis.opendocument.spreadsheet',
    'application/vnd.oasis.opendocument.spreadsheet-template',
    'application/vnd.oasis.opendocument.text',
    'application/vnd.oasis.opendocument.text-master',
    'application/vnd.oasis.opendocument.text-template',
    'application/vnd.oasis.opendocument.text-web',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.template',
    'application/vnd.openxmlformats-officedocument.presentationml.template',
    'application/vnd.openxmlformats-officedocument.presentationml.slideshow',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/vnd.openxmlformats-officedocument.presentationml.slide',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.template',
    'application/vnd.ms-office',
    'application/xml',
    'text/x-c',
    'text/x-c++',
    'text/x-pascal',
    'text/x-msdos-batch',
    'text/x-python',
    'text/x-shellscript',
    'text/plain',
    'text/rtf'
)

# Extension of the temporary copy given to LibreOffice, for the formats that
# its content detection does not always recognize without one.
CONVERTER_OFFICE_FILE_EXTENSIONS = {
    'text/rtf': '.rtf'
}

if platform.system() in ('FreeBSD', 'OpenBSD', 'Darwin'):
    DEFAULT_LIBREOFFICE_PATH = '/usr/local/bin/libreoffice'
    DEFAULT_PDFINFO_PATH = '/usr/local/bin/pdfinfo'
    DEFAULT_PDFTOPPM_PATH = '/usr/local/bin/pdftoppm'
else:
    DEFAULT_LIBREOFFICE_PATH = '/usr/bin/libreoffice'
    DEFAULT_PDFINFO_PATH = '/usr/bin/pdfinfo'
    DEFAULT_PDFTOPPM_PATH = '/usr/bin/pdftoppm'

DEFAULT_CONVERTER_ASSET_CACHE_MAXIMUM_SIZE = 10 * 2 ** 20
DEFAULT_CONVERTER_ASSET_CACHE_STORAGE_BACKEND = 'django.core.files.storage.FileSystemStorage'
DEFAULT_CONVERTER_ASSET_CACHE_STORAGE_BACKEND_ARGUMENTS = {
    'location': os.path.join(settings.MEDIA_ROOT, 'converter_assets_cache')
}
DEFAULT_CONVERTER_ASSET_STORAGE_BACKEND = 'django.core.files.storage.FileSystemStorage'
DEFAULT_CONVERTER_ASSET_STORAGE_BACKEND_ARGUMENTS = {
    'location': os.path.join(settings.MEDIA_ROOT, 'converter_assets')
}
DEFAULT_CONVERTER_COMMAND_TIMEOUT = 300
DEFAULT_CONVERTER_GRAPHICS_BACKEND = 'mayan.apps.converter.backends.python.Python'

DEFAULT_CONVERTER_IMAGE_CACHE_TIME = 31556926
DEFAULT_CONVERTER_IMAGE_CAROUSEL_REQUEST_CONCURRENCY = 4
DEFAULT_CONVERTER_IMAGE_CAROUSEL_REQUEST_RATE = 0
DEFAULT_CONVERTER_IMAGE_CAROUSEL_RETRY_ATTEMPT_MAXIMUM = 6
DEFAULT_CONVERTER_IMAGE_CAROUSEL_RETRY_DELAY_INITIAL = 500
DEFAULT_CONVERTER_IMAGE_CAROUSEL_RETRY_DELAY_MAXIMUM = 20000
DEFAULT_CONVERTER_IMAGE_GENERATION_MAX_RETRIES = 30
DEFAULT_CONVERTER_IMAGE_GENERATION_RETRY_DELAY = 4
DEFAULT_CONVERTER_IMAGE_GENERATION_TIMEOUT = 120
IMAGE_CAROUSEL_REQUEST_RATE_FACTOR = 0.8

DEFAULT_CONVERTER_LOAD_TRUNCATED_IMAGES = False

DEFAULT_LIBREOFFICE_ARGUMENTS = ''
DEFAULT_LIBREOFFICE_ENVIRONMENT = {}

DEFAULT_PAGE_NUMBER = 1
DEFAULT_PDFTOPPM_DPI = 300
DEFAULT_PDFTOPPM_FORMAT = 'jpeg'
DEFAULT_PDF_EXPORT_PAGE_SHORT_SIDE_INCHES = 8.5
DEFAULT_PILLOW_FORMAT = 'JPEG'
DEFAULT_PILLOW_MAXIMUM_IMAGE_PIXELS = 89478485
DEFAULT_ROTATION = 0
DEFAULT_TEXT_FONT_SIZE = 48
DEFAULT_THUMBNAIL_CLICK_BEHAVIOR = 'image_preview'
DEFAULT_ZOOM_LEVEL = 100

DEFAULT_CONVERTER_GRAPHICS_BACKEND_ARGUMENTS = {
    'libreoffice_arguments': DEFAULT_LIBREOFFICE_ARGUMENTS,
    'libreoffice_environment': DEFAULT_LIBREOFFICE_ENVIRONMENT,
    'libreoffice_path': DEFAULT_LIBREOFFICE_PATH,
    'pdftoppm_dpi': DEFAULT_PDFTOPPM_DPI,
    'pdftoppm_format': DEFAULT_PDFTOPPM_FORMAT,
    'pdftoppm_path': DEFAULT_PDFTOPPM_PATH,
    'pdfinfo_path': DEFAULT_PDFINFO_PATH,
    'pillow_format': DEFAULT_PILLOW_FORMAT,
    'pillow_maximum_image_pixels': DEFAULT_PILLOW_MAXIMUM_IMAGE_PIXELS
}

IMAGE_ERROR_BROKEN_FILE = 'converter_image_error_broken_file'
IMAGE_ERROR_IMAGE_BUSY = 'converter_image_error_image_busy'
IMAGE_ERROR_REQUEST_THROTTLED = 'converter_image_error_request_throttled'
IMAGE_ERROR_UNEXPECTED = 'converter_image_error_unexpected'

INTERMEDIATE_FILE_GENERATION_MAXIMUM_ATTEMPTS = 3

MAP_PILLOW_FORMAT_TO_MIME_TYPE = {
    'JPEG': 'image/jpeg'
}

PDF_EXPORT_IMAGE_MODES = ('1', 'CMYK', 'L', 'RGB')

STORAGE_NAME_ASSETS = 'converter__assets'
STORAGE_NAME_ASSETS_CACHE = 'converter__assets_cache'

TRANSFORMATION_MARKER = 'transformation_'
TRANSFORMATION_SEPARATOR = '_'
