from django.apps import apps

from mayan.apps.navigation.column_widgets import SourceColumnWidget

from .icons import icon_index_instance_node_with_documents, icon_index_level_up


class IndexInstanceNodeLinkWidget(SourceColumnWidget):
    template_name = 'document_indexing/column_widgets/index_instance_node_link.html'

    def get_extra_context(self):
        full_path = self.value.get_full_path()
        url = self.value.get_absolute_url()

        return {'full_path': full_path, 'url': url}


class IndexInstanceItemLinkWidget(SourceColumnWidget):
    template_name = 'document_indexing/column_widgets/index_instance_item_link.html'

    def get_extra_context(self):
        IndexInstanceNode = apps.get_model(
            app_label='document_indexing', model_name='IndexInstanceNode'
        )

        index_instance_item = self.value

        if isinstance(index_instance_item, IndexInstanceNode):
            if index_instance_item.index_template_node.link_documents:
                icon = icon_index_instance_node_with_documents
            else:
                icon = icon_index_level_up
        else:
            icon = None

        url = index_instance_item.get_absolute_url()

        return {'icon': icon, 'text': index_instance_item, 'url': url}


class IndexTemplateNodeLevelWidget(SourceColumnWidget):
    template_name = 'document_indexing/column_widgets/index_template_node_level.html'

    def get_extra_context(self):
        node = self.value

        if node.is_root_node():
            icon = None
        else:
            icon = icon_index_level_up

        next_level = node.get_level()

        return {
            'icon': icon, 'level_range': range(next_level), 'text': node
        }
