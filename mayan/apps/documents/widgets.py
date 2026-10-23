from django.apps import apps
from django.template.loader import render_to_string

from mayan.apps.converter.transformations import TransformationResize
from mayan.apps.converter.utils import get_object_image_data
from mayan.apps.forms import form_widgets

from .settings import (
    setting_preview_height, setting_preview_width,
    setting_thumbnail_click_behavior
)


class CarouselWidget(form_widgets.Widget):
    template_name = 'documents/forms/widgets/page_carousel.html'
    target_view = None

    def __init__(self, attrs=None):
        default_attrs = {'target_view': self.target_view}

        if attrs:
            default_attrs.update(attrs)

        super().__init__(default_attrs)

    def format_value(self, value):
        if value == '' or value is None:
            return None
        return value

    page_queryset_prefetch_related = ()
    page_queryset_select_related = ()

    def get_context(self, name, value, attrs):
        context = super().get_context(
            name=name, value=value, attrs=attrs
        )

        page_list = self.get_page_list(value=value)

        context['widget']['page_list'] = page_list
        context['widget']['page_total'] = len(page_list)

        return context

    def get_page_list(self, value):
        if value is None:
            return []

        page_list = list(
            self.get_page_queryset(value=value)
        )

        if not page_list:
            return []

        user = self.attrs.get('user', None)

        stored_transformation_map = self.get_stored_transformation_map(
            page_list=page_list, user=user
        )

        transformation_instance_list = self.attrs.get(
            'transformation_instance_list', ()
        )

        result = []

        for page in page_list:
            result.append(
                {
                    'image_data': get_object_image_data(
                        obj=page,
                        transformation_instance_list=transformation_instance_list,
                        user=user,
                        _stored_transformation_list=stored_transformation_map[page.pk]
                    ),
                    'instance': page
                }
            )

        return result

    def get_page_queryset(self, value):
        queryset = value.pages

        if self.page_queryset_select_related:
            queryset = queryset.select_related(
                *self.page_queryset_select_related
            )

        if self.page_queryset_prefetch_related:
            queryset = queryset.prefetch_related(
                *self.page_queryset_prefetch_related
            )

        return queryset

    def get_stored_transformation_map(self, page_list, user):
        LayerTransformation = apps.get_model(
            app_label='converter', model_name='LayerTransformation'
        )

        return LayerTransformation.objects.get_for_object_list(
            as_classes=True, object_list=page_list, user=user
        )


class DocumentFilePagesCarouselWidget(CarouselWidget):
    page_queryset_select_related = ('document_file',)
    target_view = 'documents:document_file_page_view'


class ThumbnailFormWidget(form_widgets.Widget):
    def render(self, *args, **kwargs):
        instance = kwargs['value']
        if instance:
            transformation_instance_list = (
                TransformationResize(
                    width=setting_preview_width.value,
                    height=setting_preview_height.value
                ),
            )

            context = {
                'disable_title_link': instance.is_in_trash,
                'gallery_name': 'document_list',
                'instance': instance,
                'thumbnail_click_behavior': setting_thumbnail_click_behavior.value,
                'transformation_instance_list': transformation_instance_list
            }
        else:
            context = {}
        return render_to_string(
            template_name='documents/widgets/thumbnail.html',
            context=context
        )


class DocumentVersionPagesCarouselWidget(CarouselWidget):
    page_queryset_prefetch_related = ('content_object',)
    page_queryset_select_related = ('document_version',)
    target_view = 'documents:document_version_page_view'

    def get_stored_transformation_map(self, page_list, user):
        LayerTransformation = apps.get_model(
            app_label='converter', model_name='LayerTransformation'
        )

        content_object_list = [
            page.content_object for page in page_list if page.content_object
        ]

        content_object_map = LayerTransformation.objects.get_for_object_list(
            as_classes=True, object_list=content_object_list, user=user
        )

        page_map = LayerTransformation.objects.get_for_object_list(
            as_classes=True, object_list=page_list, user=user
        )

        result = {}

        for page in page_list:
            entry = []

            if page.content_object:
                entry.extend(
                    content_object_map[page.content_object.pk]
                )

            entry.extend(
                page_map[page.pk]
            )

            result[page.pk] = entry

        return result


class PageImageWidget(form_widgets.Widget):
    template_name = 'documents/forms/widgets/page_image_interactive.html'

    def format_value(self, value):
        if value == '' or value is None:
            return None
        return value
