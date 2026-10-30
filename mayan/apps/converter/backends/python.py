import io
import logging
import math
import re
import shutil
import struct

from PIL import Image
import pypdf
import sh

from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from mayan.apps.storage.utils import NamedTemporaryFile, get_file_object_path

from ..classes import ConverterBase
from ..exceptions import PageCountError
from ..literals import (
    CONVERTER_DICOM_MIME_TYPES, CONVERTER_DJVU_MIME_TYPES,
    CONVERTER_DXF_MIME_TYPES, CONVERTER_EML_MIME_TYPE,
    CONVERTER_EPUB_MIME_TYPE, CONVERTER_MARKDOWN_MIME_TYPES,
    CONVERTER_RAW_PHOTO_MIME_TYPES, CONVERTER_STL_MIME_TYPES,
    CONVERTER_SVG_MIME_TYPE,
    CONVERTER_VIDEO_MIME_TYPES, DEFAULT_DJVU_PATH, DEFAULT_DJVUSED_PATH,
    DEFAULT_EBOOK_CONVERT_PATH, DEFAULT_FFMPEG_PATH, DEFAULT_PDFTOPPM_DPI,
    DEFAULT_PDFTOPPM_FORMAT, DEFAULT_PDFTOPPM_PATH, DEFAULT_PDFINFO_PATH,
    DEFAULT_PILLOW_MAXIMUM_IMAGE_PIXELS
)
from ..settings import (
    get_command_timeout, setting_graphics_backend_arguments
)

logger = logging.getLogger(name=__name__)
pdftoppm_path = setting_graphics_backend_arguments.value.get(
    'pdftoppm_path', DEFAULT_PDFTOPPM_PATH
)

try:
    command_pdftoppm = sh.Command(path=pdftoppm_path)
except sh.CommandNotFound:
    command_pdftoppm = None
else:
    pdftoppm_format = '-{}'.format(
        setting_graphics_backend_arguments.value.get(
            'pdftoppm_format', DEFAULT_PDFTOPPM_FORMAT
        )
    )

    pdftoppm_dpi = format(
        setting_graphics_backend_arguments.value.get(
            'pdftoppm_dpi', DEFAULT_PDFTOPPM_DPI
        )
    )

    command_pdftoppm = command_pdftoppm.bake(
        pdftoppm_format, '-r', pdftoppm_dpi
    )

pdfinfo_path = setting_graphics_backend_arguments.value.get(
    'pdfinfo_path', DEFAULT_PDFINFO_PATH
)

try:
    command_pdfinfo = sh.Command(path=pdfinfo_path)
except sh.CommandNotFound:
    command_pdfinfo = None


pillow_maximum_image_pixels = setting_graphics_backend_arguments.value.get(
    'pillow_maximum_image_pixels', DEFAULT_PILLOW_MAXIMUM_IMAGE_PIXELS
)
Image.MAX_IMAGE_PIXELS = pillow_maximum_image_pixels

ffmpeg_path = setting_graphics_backend_arguments.value.get(
    'ffmpeg_path', DEFAULT_FFMPEG_PATH
)
try:
    command_ffmpeg = sh.Command(path=ffmpeg_path)
except sh.CommandNotFound:
    command_ffmpeg = None

djvu_path = setting_graphics_backend_arguments.value.get(
    'ddjvu_path', DEFAULT_DJVU_PATH
)
djvused_path = setting_graphics_backend_arguments.value.get(
    'djvused_path', DEFAULT_DJVUSED_PATH
)
try:
    command_ddjvu = sh.Command(path=djvu_path)
    command_djvused = sh.Command(path=djvused_path)
except sh.CommandNotFound:
    command_ddjvu = None
    command_djvused = None

ebook_convert_path = setting_graphics_backend_arguments.value.get(
    'ebook_convert_path', DEFAULT_EBOOK_CONVERT_PATH
)
try:
    command_ebook_convert = sh.Command(path=ebook_convert_path)
except sh.CommandNotFound:
    command_ebook_convert = None


class Python(ConverterBase):
    def convert(self, *args, **kwargs):
        super().convert(*args, **kwargs)

        if self.mime_type == CONVERTER_SVG_MIME_TYPE:
            import cairosvg
            self.file_object.seek(0)
            png_bytes = cairosvg.svg2png(file_obj=self.file_object)
            self.file_object.seek(0)
            return Image.open(fp=io.BytesIO(png_bytes))

        if self.mime_type in CONVERTER_VIDEO_MIME_TYPES:
            return self._convert_video()

        if self.mime_type in CONVERTER_RAW_PHOTO_MIME_TYPES:
            return self._convert_raw_photo()

        if self.mime_type in CONVERTER_DJVU_MIME_TYPES:
            return self._convert_djvu()

        if self.mime_type == CONVERTER_EML_MIME_TYPE:
            return self._convert_eml()

        if self.mime_type in CONVERTER_MARKDOWN_MIME_TYPES:
            return self._convert_markdown()

        if self.mime_type in CONVERTER_DXF_MIME_TYPES or self._is_dxf_text():
            return self._convert_dxf()

        if self.mime_type in CONVERTER_STL_MIME_TYPES or self._is_stl_file():
            return self._convert_stl()

        if self.mime_type == CONVERTER_EPUB_MIME_TYPE or self._is_epub_zip():
            return self._convert_epub()

        if self.mime_type in CONVERTER_DICOM_MIME_TYPES:
            return self._convert_dicom()

        if self.mime_type == 'application/pdf' and command_pdftoppm:
            # A PDF stored as a plain file is read in place: copying the
            # whole file for each page filled the temporary directory with
            # large PDFs, several pages being rendered at the same time.
            path = get_file_object_path(file_object=self.file_object)
            if path:
                return self._get_pdftoppm_page_image(path=path)

            with NamedTemporaryFile() as new_file_object:
                self.file_object.seek(0)
                shutil.copyfileobj(
                    fsrc=self.file_object, fdst=new_file_object
                )
                self.file_object.seek(0)
                new_file_object.seek(0)

                return self._get_pdftoppm_page_image(
                    path=new_file_object.name
                )

    def _get_pdftoppm_page_image(self, path, resolution=None):
        arguments = (path,)
        if resolution:
            # Given after the baked arguments, it replaces their resolution.
            arguments += ('-r', resolution)

        image_buffer = io.BytesIO()
        command_pdftoppm(
            *arguments, f=self.page_number + 1, l=self.page_number + 1,
            _out=image_buffer, _timeout=get_command_timeout()
        )
        image_buffer.seek(0)

        try:
            return Image.open(fp=image_buffer)
        except Image.DecompressionBombError:
            # Oversized pages, such as captures of whole web pages, exceed
            # the pixel limit of Pillow at the configured resolution (and the
            # image size that Tesseract reads): render them at a lower one.
            reduced_resolution = None
            if not resolution:
                reduced_resolution = self._get_pdftoppm_reduced_resolution(
                    path=path
                )

            if not reduced_resolution:
                raise

            logger.warning(
                'Page %d of "%s" rendered at %d dpi instead of %s, its image '
                'exceeding the maximum number of pixels.',
                self.page_number + 1, path, reduced_resolution, pdftoppm_dpi
            )
            return self._get_pdftoppm_page_image(
                path=path, resolution=reduced_resolution
            )

    def _get_pdftoppm_reduced_resolution(self, path):
        """
        Resolution at which the page fits within the pixel limit of Pillow,
        from its size given by pdfinfo; None when it cannot be determined.
        """
        if not command_pdfinfo or not Image.MAX_IMAGE_PIXELS:
            return None

        page_number = self.page_number + 1
        try:
            output = command_pdfinfo(
                path, f=page_number, l=page_number,
                _timeout=get_command_timeout()
            )
        except (sh.ErrorReturnCode, sh.TimeoutException):
            return None

        match = re.search(
            pattern=r'size:\s+([\d.]+) x ([\d.]+) pts', string=str(output)
        )
        if not match:
            return None

        width, height = (float(points) / 72 for points in match.groups())
        resolution = int(
            math.sqrt(Image.MAX_IMAGE_PIXELS / (width * height))
        )

        if 0 < resolution < float(pdftoppm_dpi):
            return resolution

    def get_page_count(self):
        # Content-based detections that overlap with CONVERTER_OFFICE_FILE_MIMETYPES
        # (e.g. text/plain) must be checked before super() to avoid triggering
        # the LibreOffice path.
        if self.mime_type in CONVERTER_DXF_MIME_TYPES or self._is_dxf_text():
            return 1

        if self.mime_type in CONVERTER_STL_MIME_TYPES or self._is_stl_file():
            return 1

        super().get_page_count()

        try:
            if self.mime_type == CONVERTER_SVG_MIME_TYPE:
                return 1

            if self.mime_type in CONVERTER_VIDEO_MIME_TYPES:
                return 1

            if self.mime_type in CONVERTER_RAW_PHOTO_MIME_TYPES:
                return 1

            if self.mime_type in CONVERTER_DJVU_MIME_TYPES:
                return self._get_djvu_page_count()

            if self.mime_type == CONVERTER_EPUB_MIME_TYPE or self._is_epub_zip():
                # Already converted by to_pdf() in super().get_page_count().
                return self.get_pypdf_page_count(file_object=self.soffice_file)

            if self.mime_type in CONVERTER_MARKDOWN_MIME_TYPES:
                return self._get_markdown_page_count()

            if self.mime_type in (
                CONVERTER_EML_MIME_TYPE,
                *CONVERTER_DXF_MIME_TYPES,
                *CONVERTER_STL_MIME_TYPES,
                *CONVERTER_DICOM_MIME_TYPES,
            ) or self._is_dxf_text() or self._is_stl_file():
                return 1

            if self.mime_type == 'application/pdf' or self.soffice_file:
                if self.soffice_file:
                    file_object = self.soffice_file
                else:
                    file_object = self.file_object

                return self.get_pypdf_page_count(file_object=file_object)
            else:
                return self.get_pillow_page_count()
        finally:
            if self.soffice_file:
                self.soffice_file.close()
                self.soffice_file = None

    def to_pdf(self):
        # EPUB files are converted as a whole, like office documents, so that
        # ConverterBase.get_intermediate_file() keeps the PDF in the cache
        # instead of Calibre converting the book again for each page.
        if self.mime_type == CONVERTER_EPUB_MIME_TYPE or self._is_epub_zip():
            temporary_file_object = NamedTemporaryFile()
            temporary_file_object.write(
                self._epub_to_pdf_bytes()
            )
            temporary_file_object.seek(0)
            return temporary_file_object

        return super().to_pdf()

    def get_pillow_page_count(self):
        page_count = 1

        try:
            image = Image.open(fp=self.file_object)
        except IOError as exception:
            error_message = _(
                message='Exception determining page count using Pillow; %s'
            ) % exception
            logger.error(error_message)
            raise PageCountError(error_message)
        finally:
            self.file_object.seek(0)

        while True:
            try:
                image.seek(
                    image.tell() + 1
                )
            except EOFError:
                """End of sequence"""
                break
            except struct.error:
                """
                struct.error was raise for a TIFF file converted to JPEG
                GitLab issue #767 "Upload Error: unpack_from requires a
                buffer of at least 2 bytes"
                """
                logger.debug(
                    msg='image page count detection raised struct.error'
                )
                break
            else:
                try:
                    image.getim()
                except OSError as exception:
                    logger.error(
                        'Multi image element not supported; %s',
                        exception
                    )
                    break
                else:
                    page_count += 1

        self.file_object.seek(0)
        return page_count

    def get_pdfinfo_page_count(self, file_object):
        if command_pdfinfo is None:
            file_object.seek(0)
            error_message = _(
                message='Exception determining PDF page count; pdfinfo '
                '(poppler-utils) is not installed.'
            )
            logger.error(error_message)
            raise PageCountError(error_message)

        try:
            process = command_pdfinfo(
                '-', _in=file_object, _timeout=get_command_timeout()
            )
        except sh.TimeoutException:
            file_object.seek(0)
            error_message = _(
                message='Exception determining PDF page count; pdfinfo did '
                'not finish before the command timeout and was terminated.'
            )
            logger.error(error_message)
            raise PageCountError(error_message)

        page_count = None
        for line in force_str(s=process.stdout).split('\n'):
            if line.startswith('Pages:'):
                line = line.replace('Pages:', '')
                page_count = int(line)
                break

        file_object.seek(0)

        if page_count is None:
            error_message = _(
                message='Exception determining PDF page count; pdfinfo did '
                'not report a page count.'
            )
            logger.error(error_message)
            raise PageCountError(error_message)

        logger.debug('Document contains %d pages', page_count)
        return page_count

    def get_pypdf_page_count(self, file_object):
        try:
            pdf_reader = pypdf.PdfReader(
                stream=file_object, strict=False
            )
            page_count = len(pdf_reader.pages)
        except Exception as exception:
            if str(exception) == 'File has not been decrypted':
                file_object.seek(0)
                pdf_reader = pypdf.PdfReader(
                    stream=file_object, strict=False
                )
                try:
                    pdf_reader.decrypt(password=b'')
                    page_count = len(pdf_reader.pages)
                except Exception as exception:
                    file_object.seek(0)
                    if str(exception) == 'only algorithm code 1 and 2 are supported':
                        page_count = self.get_pdfinfo_page_count(
                            file_object=file_object
                        )
                        return page_count
                    else:
                        error_message = _(
                            message='Exception determining PDF page count; %s'
                        ) % exception
                        logger.error(error_message, exc_info=True)
                        raise PageCountError(error_message)
            elif str(exception) == 'EOF marker not found':
                logger.debug(
                    msg='PyPDF2 GitHub issue #177 : EOF marker not found'
                )
                file_object.seek(0)
                page_count = self.get_pdfinfo_page_count(
                    file_object=file_object
                )
                return page_count
            else:
                error_message = _(
                    message='Exception determining PDF page count; %s'
                ) % exception
                logger.error(error_message, exc_info=True)
                raise PageCountError(error_message)
        else:
            logger.debug('Document contains %d pages', page_count)
            return page_count
        finally:
            file_object.seek(0)

    # ── Conversions spécialisées ──────────────────────────────────────────────

    def _convert_video(self):
        if not command_ffmpeg:
            raise PageCountError('ffmpeg not installed or not found.')
        with NamedTemporaryFile(suffix='.jpg') as out_file:
            self.file_object.seek(0)
            with NamedTemporaryFile(suffix='.bin') as in_file:
                shutil.copyfileobj(self.file_object, in_file)
                self.file_object.seek(0)
                in_file.seek(0)
                command_ffmpeg(
                    '-y', '-i', in_file.name,
                    '-vframes', '1', '-ss', '0',
                    '-f', 'image2', out_file.name
                )
            out_file.seek(0)
            return Image.open(fp=io.BytesIO(out_file.read()))

    def _convert_raw_photo(self):
        import rawpy
        import numpy as np
        with NamedTemporaryFile(suffix='.raw') as tmp:
            self.file_object.seek(0)
            shutil.copyfileobj(self.file_object, tmp)
            self.file_object.seek(0)
            tmp.flush()
            with rawpy.imread(tmp.name) as raw:
                rgb = raw.postprocess()
        return Image.fromarray(rgb)

    def _convert_djvu(self):
        if not command_ddjvu:
            raise PageCountError('djvulibre (ddjvu) not installed or not found.')
        page_number = getattr(self, 'page_number', 0)
        with NamedTemporaryFile(suffix='.djvu') as in_file:
            self.file_object.seek(0)
            shutil.copyfileobj(self.file_object, in_file)
            self.file_object.seek(0)
            in_file.flush()
            image_buffer = io.BytesIO()
            try:
                command_ddjvu(
                    '-format=ppm',
                    '-page={}'.format(page_number + 1),
                    in_file.name, '-',
                    _out=image_buffer
                )
            except Exception as exception:
                raise PageCountError(
                    'ddjvu failed to render DjVu page {} (the file may be '
                    'in indirect/paged format — only bundled single-file DjVu '
                    'is supported): {}'.format(page_number + 1, exception)
                )
            image_buffer.seek(0)
            return Image.open(fp=image_buffer)

    def _get_djvu_page_count(self):
        if not command_djvused:
            return 1
        with NamedTemporaryFile(suffix='.djvu') as tmp:
            self.file_object.seek(0)
            shutil.copyfileobj(self.file_object, tmp)
            self.file_object.seek(0)
            tmp.flush()
            try:
                output = str(command_djvused(tmp.name, '-e', 'n'))
                return int(output.strip())
            except Exception:
                return 1

    def _convert_eml(self):
        import email as email_lib
        import weasyprint
        self.file_object.seek(0)
        msg = email_lib.message_from_binary_file(
            self.file_object, policy=email_lib.policy.default
        )
        self.file_object.seek(0)

        subject = msg.get('Subject', '(no subject)')
        from_addr = msg.get('From', '')
        to_addr = msg.get('To', '')
        date = msg.get('Date', '')

        body = ''
        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                if ct == 'text/html':
                    body = part.get_payload(decode=True).decode(
                        part.get_content_charset() or 'utf-8', errors='replace'
                    )
                    break
                if ct == 'text/plain' and not body:
                    body = '<pre>{}</pre>'.format(
                        part.get_payload(decode=True).decode(
                            part.get_content_charset() or 'utf-8', errors='replace'
                        )
                    )
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body = '<pre>{}</pre>'.format(
                    payload.decode(msg.get_content_charset() or 'utf-8', errors='replace')
                )

        html = (
            '<!DOCTYPE html><html><head>'
            '<meta charset="utf-8">'
            '<style>body{{font-family:sans-serif;margin:2em;}} '
            '.header{{background:#f5f5f5;padding:1em;border-radius:4px;margin-bottom:1em;}} '
            '.label{{color:#666;font-size:.85em;}} pre{{white-space:pre-wrap;}}</style>'
            '</head><body>'
            '<div class="header">'
            '<div><span class="label">De&nbsp;:</span> {from_}</div>'
            '<div><span class="label">À&nbsp;:</span> {to}</div>'
            '<div><span class="label">Date&nbsp;:</span> {date}</div>'
            '<div><span class="label">Objet&nbsp;:</span> <strong>{subject}</strong></div>'
            '</div>{body}</body></html>'
        ).format(
            from_=from_addr, to=to_addr, date=date,
            subject=subject, body=body
        )

        pdf_bytes = weasyprint.HTML(string=html).write_pdf()
        return self._pdf_bytes_to_image(pdf_bytes)

    def _markdown_to_pdf_bytes(self):
        import markdown as md_lib
        import weasyprint
        self.file_object.seek(0)
        text = self.file_object.read().decode('utf-8', errors='replace')
        self.file_object.seek(0)
        html_body = md_lib.markdown(
            text, extensions=['tables', 'fenced_code', 'toc']
        )
        html = (
            '<!DOCTYPE html><html><head><meta charset="utf-8">'
            '<style>body{{font-family:sans-serif;max-width:800px;margin:2em auto;line-height:1.6;}} '
            'code{{background:#f4f4f4;padding:.2em .4em;border-radius:3px;}} '
            'pre code{{display:block;padding:1em;}} '
            'table{{border-collapse:collapse;width:100%;}} '
            'th,td{{border:1px solid #ddd;padding:.5em;}} '
            'th{{background:#f5f5f5;}}</style>'
            '</head><body>{}</body></html>'
        ).format(html_body)
        return weasyprint.HTML(string=html).write_pdf()

    def _get_markdown_page_count(self):
        return self.get_pypdf_page_count(
            file_object=io.BytesIO(self._markdown_to_pdf_bytes())
        )

    def _convert_markdown(self):
        page_number = getattr(self, 'page_number', 0)
        return self._pdf_bytes_to_image(
            self._markdown_to_pdf_bytes(), page_number=page_number
        )

    def _convert_dxf(self):
        import matplotlib.pyplot as plt
        plt.switch_backend('agg')
        import ezdxf
        from ezdxf.addons.drawing import RenderContext, Frontend
        from ezdxf.addons.drawing.config import (
            Configuration, ColorPolicy, BackgroundPolicy,
        )
        from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

        with NamedTemporaryFile(suffix='.dxf') as tmp:
            self.file_object.seek(0)
            shutil.copyfileobj(self.file_object, tmp)
            self.file_object.seek(0)
            tmp.flush()
            doc = ezdxf.readfile(tmp.name)

        fig = plt.figure(figsize=(12, 9), facecolor='white')
        ax = fig.add_axes([0, 0, 1, 1], facecolor='white')
        ax.set_axis_off()
        ax.set_aspect('equal')
        ctx = RenderContext(doc)
        backend = MatplotlibBackend(ax)
        # MONOCHROME_LIGHT_BG forces all entities to black on white regardless
        # of ACI color, avoiding invisible entities (e.g. ACI 250 = #000000
        # would be swapped to white by COLOR_SWAP_BW).
        config = Configuration(
            color_policy=ColorPolicy.MONOCHROME_LIGHT_BG,
            background_policy=BackgroundPolicy.WHITE,
        )
        Frontend(ctx, backend, config=config).draw_layout(doc.modelspace())
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor='white')
        plt.close(fig)
        buf.seek(0)
        return Image.open(fp=buf)

    def _is_dxf_text(self):
        """Return True if this text/plain file is an ASCII DXF (group code 0 + SECTION)."""
        if self.mime_type != 'text/plain':
            return False
        try:
            self.file_object.seek(0)
            raw = self.file_object.read(256)
            self.file_object.seek(0)
            text = raw.decode('ascii', errors='ignore')
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            for i in range(min(len(lines) - 1, 8)):
                if lines[i] == '0' and lines[i + 1] == 'SECTION':
                    return True
            return False
        except Exception:
            self.file_object.seek(0)
            return False

    def _is_stl_file(self):
        """Return True if the file is an ASCII or binary STL."""
        if self.mime_type in CONVERTER_STL_MIME_TYPES:
            return True
        try:
            self.file_object.seek(0)
            header = self.file_object.read(256)
            self.file_object.seek(0)
            # ASCII STL starts with 'solid'
            if header.lstrip()[:5].lower() == b'solid':
                return True
            # Binary STL: 80-byte header + 4-byte uint32 count + count*50 bytes
            if len(header) >= 84:
                import struct
                count = struct.unpack_from('<I', header, 80)[0]
                self.file_object.seek(0, 2)
                size = self.file_object.tell()
                self.file_object.seek(0)
                if count > 0 and size == 84 + count * 50:
                    return True
            return False
        except Exception:
            self.file_object.seek(0)
            return False

    def _convert_stl(self):
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        from stl import mesh as stl_mesh
        import numpy as np

        with NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
            self.file_object.seek(0)
            shutil.copyfileobj(self.file_object, tmp)
            self.file_object.seek(0)
            tmp.flush()
            tmp_name = tmp.name

        model = stl_mesh.Mesh.from_file(tmp_name)
        import os; os.unlink(tmp_name)

        vectors = model.vectors  # shape (N, 3, 3)

        fig = plt.figure(figsize=(10, 10), facecolor='white')
        ax = fig.add_subplot(111, projection='3d', facecolor='white')

        poly = Poly3DCollection(
            vectors,
            alpha=0.85,
            facecolor='#c8d8e8',
            edgecolor='#4a6a8a',
            linewidth=0.2,
        )
        ax.add_collection3d(poly)

        # Auto-scale axes to the mesh bounds
        pts = vectors.reshape(-1, 3)
        for dim, setter in enumerate((ax.set_xlim, ax.set_ylim, ax.set_zlim)):
            setter(pts[:, dim].min(), pts[:, dim].max())

        ax.set_box_aspect([
            float(pts[:, 0].max() - pts[:, 0].min()) or 1,
            float(pts[:, 1].max() - pts[:, 1].min()) or 1,
            float(pts[:, 2].max() - pts[:, 2].min()) or 1,
        ])
        ax.view_init(elev=25, azim=45)
        ax.set_axis_off()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor='white')
        plt.close(fig)
        buf.seek(0)
        return Image.open(fp=buf)

    def _is_epub_zip(self):
        """Return True if file is a ZIP that contains META-INF/container.xml (EPUB)."""
        if self.mime_type != 'application/zip':
            return False
        return self.is_epub_zip(file_object=self.file_object)

    def _epub_to_pdf_bytes(self):
        if not command_ebook_convert:
            raise PageCountError(
                'ebook-convert (calibre) not installed or not found at '
                '{}.'.format(ebook_convert_path)
            )
        import os
        import tempfile
        with NamedTemporaryFile(suffix='.epub') as in_file:
            self.file_object.seek(0)
            shutil.copyfileobj(self.file_object, in_file)
            self.file_object.seek(0)
            in_file.flush()
            fd, out_path = tempfile.mkstemp(suffix='.pdf')
            os.close(fd)
            os.unlink(out_path)
            try:
                command_ebook_convert(
                    in_file.name, out_path, _timeout=get_command_timeout()
                )
                with open(out_path, 'rb') as f:
                    return f.read()
            except (sh.ErrorReturnCode, sh.TimeoutException) as exception:
                raise PageCountError(
                    'Error converting the EPUB file to PDF with Calibre; '
                    '{}'.format(exception)
                ) from exception
            finally:
                try:
                    os.unlink(out_path)
                except OSError:
                    pass

    def _convert_epub(self):
        pdf_bytes = self._epub_to_pdf_bytes()
        page_number = getattr(self, 'page_number', 0)
        return self._pdf_bytes_to_image(pdf_bytes, page_number=page_number)

    def _convert_dicom(self):
        import pydicom
        import numpy as np

        self.file_object.seek(0)
        ds = pydicom.dcmread(self.file_object, force=True)
        self.file_object.seek(0)

        pixel_array = ds.pixel_array

        # Multi-frame DICOM: (frames, rows, cols) or (frames, rows, cols, 3).
        # Last dim == 3 or 4 means color channels, not frames.
        if pixel_array.ndim == 3 and pixel_array.shape[2] not in (3, 4):
            pixel_array = pixel_array[0]  # first frame → (rows, cols)
        elif pixel_array.ndim == 4:
            pixel_array = pixel_array[0]  # first frame → (rows, cols, 3)

        # Normalize to 8-bit
        arr_min, arr_max = pixel_array.min(), pixel_array.max()
        if arr_max > arr_min:
            pixel_array = (
                (pixel_array - arr_min) / (arr_max - arr_min) * 255
            ).astype('uint8')
        else:
            pixel_array = pixel_array.astype('uint8')

        if pixel_array.ndim == 2:
            return Image.fromarray(pixel_array, mode='L').convert('RGB')
        elif pixel_array.ndim == 3 and pixel_array.shape[2] == 4:
            return Image.fromarray(pixel_array, mode='RGBA').convert('RGB')
        else:
            return Image.fromarray(pixel_array)

    def _pdf_bytes_to_image(self, pdf_bytes, page_number=0):
        """Converts one page of a PDF (bytes) to Image via pdftoppm."""
        page_1indexed = str(page_number + 1)
        if command_pdftoppm:
            with NamedTemporaryFile(suffix='.pdf') as tmp:
                tmp.write(pdf_bytes)
                tmp.flush()
                buf = io.BytesIO()
                command_pdftoppm(
                    tmp.name, '-f', page_1indexed, '-l', page_1indexed,
                    _out=buf
                )
                buf.seek(0)
                return Image.open(fp=buf)
        return Image.open(fp=io.BytesIO(pdf_bytes))
