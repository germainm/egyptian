from django.utils.translation import gettext_lazy as _

from mayan.apps.dependencies.classes import BinaryDependency, PythonDependency
from mayan.apps.dependencies.environments import environment_production

from .backends.python import (
    djvu_path, djvused_path, ebook_convert_path, ffmpeg_path, pdfinfo_path,
    pdftoppm_path
)
from .classes import libreoffice_path

# ── Binaires système ──────────────────────────────────────────────────────────

BinaryDependency(
    environments=(environment_production,), label='LibreOffice',
    module=__name__, name='libreoffice', path=libreoffice_path
)
BinaryDependency(
    environments=(environment_production,), label='PDF Info', help_text=_(
        message='Utility from the poppler-utils package used to inspect PDF '
        'files.'
    ), module=__name__, name='pdfinfo', path=pdfinfo_path
)
BinaryDependency(
    environments=(environment_production,), label='PDF to PPM', help_text=_(
        message='Utility from the poppler-utils package used to extract '
        'pages from PDF files into PPM format images.'
    ), module=__name__, name='pdftoppm', path=pdftoppm_path
)
BinaryDependency(
    environments=(environment_production,), label='FFmpeg', help_text=_(
        message='Multimedia framework used to extract the first frame of '
        'video files (MP4, MKV, AVI, WebM…).'
    ), module=__name__, name='ffmpeg', path=ffmpeg_path
)
BinaryDependency(
    environments=(environment_production,), label='DjVu to PPM (ddjvu)', help_text=_(
        message='Utility from the djvulibre-bin package used to render '
        'DjVu pages as images.'
    ), module=__name__, name='ddjvu', path=djvu_path
)
BinaryDependency(
    environments=(environment_production,), label='DjVu metadata (djvused)', help_text=_(
        message='Utility from the djvulibre-bin package used to read '
        'the page count of DjVu files.'
    ), module=__name__, name='djvused', path=djvused_path
)
BinaryDependency(
    environments=(environment_production,), label='ebook-convert (Calibre)', help_text=_(
        message='Utility from the Calibre package used to convert EPUB '
        'files to PDF for page rendering.'
    ), module=__name__, name='ebook-convert', path=ebook_convert_path
)

# ── Packages Python ───────────────────────────────────────────────────────────

PythonDependency(
    attribute_copyright='PIL.__doc__',
    environments=(environment_production,), module=__name__, name='Pillow',
    version_string='==12.1.1'
)
PythonDependency(
    environments=(environment_production,), module=__name__, name='pypdf',
    version_string='==6.7.3'
)
PythonDependency(
    environments=(environment_production,), module=__name__, name='qrcode',
    version_string='==8.2'
)
PythonDependency(
    environments=(environment_production,), module=__name__, name='pillow-heif',
    version_string='==1.3.0'
)
PythonDependency(
    environments=(environment_production,), module=__name__, name='rawpy',
    version_string='==0.26.1'
)
PythonDependency(
    environments=(environment_production,), module=__name__, name='ezdxf',
    version_string='==1.4.3'
)
PythonDependency(
    environments=(environment_production,), module=__name__, name='weasyprint',
    version_string='==68.1'
)
PythonDependency(
    environments=(environment_production,), module=__name__, name='pydicom',
    version_string='==3.0.2'
)
PythonDependency(
    environments=(environment_production,), module=__name__, name='matplotlib',
    version_string='==3.10.8'
)
