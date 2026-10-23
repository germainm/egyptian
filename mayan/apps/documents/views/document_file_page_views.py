import logging

from furl import furl

from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView

from mayan.apps.common.settings import setting_home_view
from mayan.apps.converter.literals import DEFAULT_ROTATION, DEFAULT_ZOOM_LEVEL
from mayan.apps.converter.transformations import (
    TransformationResize, TransformationRotate, TransformationZoom
)
from mayan.apps.databases.classes import ModelQueryFields
from mayan.apps.views.generics import SimpleView, SingleObjectListView
from mayan.apps.views.utils import get_request_referer, resolve
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from ..forms.document_file_page_forms import DocumentFilePageForm
from ..icons import (
    icon_document_file_page_detail, icon_document_file_page_list
)
from ..links.document_file_links import link_document_file_introspect_single
from ..models.document_file_models import DocumentFile
from ..models.document_file_page_models import DocumentFilePage
from ..permissions import permission_document_file_view
from ..settings import (
    setting_display_height, setting_display_width, setting_rotation_step,
    setting_zoom_percent_step, setting_zoom_max_level, setting_zoom_min_level
)

logger = logging.getLogger(name=__name__)


class DocumentFilePageListView(
    ExternalObjectViewMixin, SingleObjectListView
):
    external_object_permission = permission_document_file_view
    external_object_pk_url_kwarg = 'document_file_id'
    external_object_queryset = DocumentFile.valid.all()
    view_icon = icon_document_file_page_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'list_as_items': True,
            'no_results_icon': icon_document_file_page_list,
            'no_results_main_link': link_document_file_introspect_single.resolve(
                request=self.request, resolved_object=self.external_object
            ),
            'no_results_text': _(
                message='This could mean that the document file is of a '
                'format that is not supported, that it is corrupted, or that '
                'the upload process was interrupted. Use the document file '
                'introspection link to attempt to detect the page count '
                'again.'
            ),
            'no_results_title': _(message='No document file pages available'),
            'object': self.external_object,
            'title': _(
                message='Pages of document file: %s'
            ) % self.external_object
        }

    def get_source_queryset(self):
        queryset = ModelQueryFields.get(
            model=DocumentFilePage
        ).get_queryset()

        return queryset.filter(
            pk__in=self.external_object.pages.all()
        )


class DocumentFilePageNavigationBase(ExternalObjectViewMixin, RedirectView):
    external_object_permission = permission_document_file_view
    external_object_pk_url_kwarg = 'document_file_page_id'
    external_object_queryset = DocumentFilePage.valid.all()

    def get_redirect_url(self, *args, **kwargs):
        previous_url = get_request_referer(request=self.request)

        if not previous_url:
            try:
                previous_url = self.external_object.get_absolute_url()
            except AttributeError:
                previous_url = reverse(viewname=setting_home_view.value)

        parsed_url = furl(url=previous_url)

        resolver_match = resolve(
            path=str(parsed_url.path)
        )

        new_kwargs = self.get_new_kwargs()

        if set(new_kwargs) == set(resolver_match.kwargs):
            url = reverse(
                kwargs=new_kwargs, viewname=resolver_match.view_name
            )
        else:
            url = parsed_url.path

        parsed_url.path = url

        return parsed_url.tostr()


class DocumentFilePageNavigationFirst(DocumentFilePageNavigationBase):
    def get_new_kwargs(self):
        return {
            'document_file_page_id': self.external_object.siblings.first().pk
        }


class DocumentFilePageNavigationLast(DocumentFilePageNavigationBase):
    def get_new_kwargs(self):
        return {
            'document_file_page_id': self.external_object.siblings.last().pk
        }


class DocumentFilePageNavigationNext(DocumentFilePageNavigationBase):
    def get_new_kwargs(self):
        new_document_file_page = self.external_object.siblings.filter(
            page_number__gt=self.external_object.page_number
        ).first()
        if new_document_file_page:
            return {'document_file_page_id': new_document_file_page.pk}
        else:
            messages.warning(
                message=_(
                    message='There are no more pages in this document'
                ), request=self.request
            )
            return {'document_file_page_id': self.external_object.pk}


class DocumentFilePageNavigationPrevious(DocumentFilePageNavigationBase):
    def get_new_kwargs(self):
        new_document_file_page = self.external_object.siblings.filter(
            page_number__lt=self.external_object.page_number
        ).last()
        if new_document_file_page:
            return {'document_file_page_id': new_document_file_page.pk}
        else:
            messages.warning(
                message=_(
                    message='You are already at the first page of this '
                    'document'
                ), request=self.request
            )
            return {'document_file_page_id': self.external_object.pk}


class DocumentFilePageView(ExternalObjectViewMixin, SimpleView):
    external_object_permission = permission_document_file_view
    external_object_pk_url_kwarg = 'document_file_page_id'
    external_object_queryset = DocumentFilePage.valid.all()
    template_name = 'appearance/viewport_fill.html'
    view_icon = icon_document_file_page_detail

    def get_extra_context(self):
        zoom = int(
            self.request.GET.get('zoom', DEFAULT_ZOOM_LEVEL)
        )
        rotation = int(
            self.request.GET.get('rotation', DEFAULT_ROTATION)
        )

        transformation_instance_list = (
            TransformationResize(
                height=setting_display_height.value,
                width=setting_display_width.value
            ),
            TransformationRotate(degrees=rotation),
            TransformationZoom(percent=zoom)
        )

        document_file_page_form = DocumentFilePageForm(
            instance=self.external_object,
            transformation_instance_list=transformation_instance_list
        )

        base_title = _(message='Image of: %s') % self.external_object

        if zoom != DEFAULT_ZOOM_LEVEL:
            zoom_text = '({}%)'.format(zoom)
        else:
            zoom_text = ''

        return {
            'form': document_file_page_form,
            'hide_labels': True,
            'object': self.external_object,
            'read_only': True,
            'rotation': rotation,
            'title': ' '.join(
                (base_title, zoom_text)
            ),
            'zoom': zoom
        }


class DocumentFilePageViewResetView(RedirectView):
    pattern_name = 'documents:document_file_page_view'


class DocumentFilePageInteractiveTransformation(
    ExternalObjectViewMixin, RedirectView
):
    external_object_permission = permission_document_file_view
    external_object_pk_url_kwarg = 'document_file_page_id'
    external_object_queryset = DocumentFilePage.valid.all()

    def get_object(self):
        return self.external_object

    def get_redirect_url(self, *args, **kwargs):
        query_dict = {
            'rotation': self.request.GET.get('rotation', DEFAULT_ROTATION),
            'zoom': self.request.GET.get('zoom', DEFAULT_ZOOM_LEVEL)
        }

        url = furl(
            args=query_dict, path=reverse(
                kwargs={'document_file_page_id': self.external_object.pk},
                viewname='documents:document_file_page_view'
            )

        )

        self.transformation_function(query_dict=query_dict)
        url.args = query_dict

        return url.tostr()


class DocumentFilePageZoomInView(DocumentFilePageInteractiveTransformation):
    def transformation_function(self, query_dict):
        zoom = int(
            query_dict['zoom']
        ) + setting_zoom_percent_step.value

        if zoom > setting_zoom_max_level.value:
            zoom = setting_zoom_max_level.value

        query_dict['zoom'] = zoom


class DocumentFilePageZoomOutView(DocumentFilePageInteractiveTransformation):
    def transformation_function(self, query_dict):
        zoom = int(
            query_dict['zoom']
        ) - setting_zoom_percent_step.value

        if zoom < setting_zoom_min_level.value:
            zoom = setting_zoom_min_level.value

        query_dict['zoom'] = zoom


class DocumentFilePageRotateLeftView(
    DocumentFilePageInteractiveTransformation
):
    def transformation_function(self, query_dict):
        query_dict['rotation'] = (
            int(
                query_dict['rotation']
            ) - setting_rotation_step.value
        ) % 360


class DocumentFilePageRotateRightView(
    DocumentFilePageInteractiveTransformation
):
    def transformation_function(self, query_dict):
        query_dict['rotation'] = (
            int(
                query_dict['rotation']
            ) + setting_rotation_step.value
        ) % 360
