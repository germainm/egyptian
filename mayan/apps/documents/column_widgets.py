from mayan.apps.converter.transformations import TransformationResize
from mayan.apps.navigation.column_widgets import SourceColumnWidget

from .settings import (
    setting_thumbnail_click_behavior, setting_thumbnail_height,
    setting_thumbnail_width
)


class SourceColumnWidgetDocumentLink(SourceColumnWidget):
    template_name = 'documents/column_widgets/document_link.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.document = self.get_document()

    def get_document(self):
        return self.value.document

    def get_extra_context(self):
        return {'instance': self.document}


class ThumbnailWidget(SourceColumnWidget):
    template_name = 'documents/widgets/thumbnail.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.document = self.get_document()

    def disable_condition(self):
        return self.document.is_in_trash

    def get_document(self):
        return self.value

    def get_extra_context(self):
        transformation_resize = TransformationResize(
            height=setting_thumbnail_height.value,
            width=setting_thumbnail_width.value
        )

        transformation_instance_list = (transformation_resize,)

        return {
            'disable_title_link': self.disable_condition(),
            'gallery_name': 'document_list',
            'instance': self.document,
            'thumbnail_click_behavior': setting_thumbnail_click_behavior.value,
            'transformation_instance_list': transformation_instance_list
        }
