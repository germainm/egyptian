import logging

from furl import furl

from django.http import Http404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.generic.base import View

from mayan.apps.common.utils import parse_range
from mayan.apps.converter.transformations import TransformationResize
from mayan.apps.converter.utils import object_list_export_to_pdf
from mayan.apps.storage.utils import TemporaryFile
from mayan.apps.storage.views.mixins import ViewMixinDownload
from mayan.apps.views.generics import FormView, SimpleView
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from ..forms.misc_forms import PrintForm
from ..literals import (
    PAGE_RANGE_RANGE, PRINT_PDF_FILENAME_EXTENSION, PRINT_PDF_MIME_TYPE
)
from ..settings import setting_print_height, setting_print_width

logger = logging.getLogger(name=__name__)


class ViewMixinDocumentPrint:
    def get_page_queryset(self):
        page_group = self.request.GET.get('page_group', None)
        page_range = self.request.GET.get('page_range', None)

        queryset = self.external_object.pages

        if page_group == PAGE_RANGE_RANGE and page_range:
            try:
                page_number_list = list(
                    parse_range(range_string=page_range)
                )
            except ValueError:
                logger.warning(
                    'Unable to parse the page range: %s', page_range
                )
            else:
                return queryset.filter(page_number__in=page_number_list)

        return queryset.all()

    def get_transformation_instance_list(self):
        return (
            TransformationResize(
                height=setting_print_height.value,
                width=setting_print_width.value
            ),
        )


class PrintFormView(ExternalObjectViewMixin, FormView):
    external_object_class = None
    external_object_permission = None
    external_object_pk_url_kwarg = None
    form_class = PrintForm
    print_view_name = None
    print_view_kwarg = None

    def _add_recent_document(self):
        self.external_object.add_as_recent_document_for_user(
            user=self.request.user
        )

    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request=request, *args, **kwargs)

        self._add_recent_document()

        return result

    def get_extra_context(self):
        return {
            'form_action': reverse(
                kwargs={self.print_view_kwarg: self.external_object.pk},
                viewname=self.print_view_name
            ),
            'object': self.external_object,
            'submit_label': _(message='Print'),
            'submit_method': 'GET',
            'submit_target': '_blank',
            'title': _(message='Print: %s') % self.external_object
        }


class DocumentPrintBaseView(
    ViewMixinDocumentPrint, ExternalObjectViewMixin, SimpleView
):
    external_object_class = None
    external_object_permission = None
    external_object_pk_url_kwarg = None
    print_pdf_view_name = None
    print_pdf_view_kwarg = None
    template_name = 'documents/document_print.html'

    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request=request, *args, **kwargs)

        self._add_recent_document()

        return result

    def get_extra_context(self):
        page_queryset = self.get_page_queryset()

        return {
            'appearance_type': 'plain',
            'page_count': page_queryset.count(),
            'print_pdf_url': self.get_print_pdf_url(),
            'title': _(message='Print: %s') % self.external_object
        }

    def get_print_pdf_url(self):
        url = furl(
            reverse(
                kwargs={
                    self.print_pdf_view_kwarg: self.external_object.pk
                }, viewname=self.print_pdf_view_name
            )
        )
        url.args.update(
            self.request.GET.dict()
        )

        return url.tostr()


@method_decorator(xframe_options_sameorigin, name='dispatch')
class DocumentPrintPDFBaseView(
    ViewMixinDocumentPrint, ViewMixinDownload, ExternalObjectViewMixin, View
):
    as_attachment = False
    external_object_class = None
    external_object_permission = None
    external_object_pk_url_kwarg = None

    def get(self, request, *args, **kwargs):
        return self.render_to_response()

    def get_download_file_object(self):
        page_list = self.get_page_queryset()
        transformation_instance_list = self.get_transformation_instance_list()

        file_object = TemporaryFile(mode='wb+')

        try:
            page_count = object_list_export_to_pdf(
                file_object=file_object, object_list=page_list,
                transformation_instance_list=transformation_instance_list,
                user=self.request.user
            )
        except Exception:
            file_object.close()
            raise

        if not page_count:
            file_object.close()
            raise Http404(
                _(message='There are no pages to print.')
            )

        file_object.seek(0)

        return file_object

    def get_download_filename(self):
        filename = str(self.external_object)

        if not filename.lower().endswith(PRINT_PDF_FILENAME_EXTENSION):
            filename = '{}{}'.format(filename, PRINT_PDF_FILENAME_EXTENSION)

        return filename

    def get_download_mime_type_and_encoding(self, file_object):
        return (PRINT_PDF_MIME_TYPE, None)
