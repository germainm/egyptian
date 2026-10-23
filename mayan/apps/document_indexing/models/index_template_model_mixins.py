from django.apps import apps

from mayan.apps.documents.models.document_models import Document
from mayan.apps.events.classes import ModelEventType

from ..events import event_index_template_edited


class IndexTemplateBusinessLogicMixin:
    def do_event_triggers_populate(self):
        IndexTemplateEventTrigger = apps.get_model(
            app_label='document_indexing',
            model_name='IndexTemplateEventTrigger'
        )

        entries = []

        for event_type in ModelEventType.get_for_class(klass=Document):
            entries.append(
                IndexTemplateEventTrigger(
                    index_template=self,
                    stored_event_type=event_type.get_stored_event_type()
                )
            )

        IndexTemplateEventTrigger.objects.bulk_create(objs=entries)

    def document_types_add(self, queryset, user):
        for document_type in queryset:
            self.document_types.add(document_type)

            event_index_template_edited.commit(
                action_object=document_type,
                actor=user, target=self
            )

    def document_types_remove(self, queryset, user):
        for document_type in queryset:
            self.document_types.remove(document_type)

            event_index_template_edited.commit(
                action_object=document_type,
                actor=user, target=self
            )

    def delete_index_instance_nodes(self):
        IndexInstanceNode = apps.get_model(
            app_label='document_indexing', model_name='IndexInstanceNode'
        )

        IndexInstanceNode.objects.filter(
            index_template_node__index=self
        ).delete()

    def get_document_types_names(self):
        return ', '.join(
            [
                str(document_type) for document_type in self.document_types.all()
            ] or ['None']
        )

    @property
    def index_template_root_node(self):
        try:
            return self._index_template_root_node
        except AttributeError:
            self._index_template_root_node = self.index_template_nodes.get(
                parent=None
            )
            return self._index_template_root_node

    def rebuild(self):
        IndexInstance = apps.get_model(
            app_label='document_indexing', model_name='IndexInstance'
        )

        if self.enabled:
            self.delete_index_instance_nodes()

            self.index_template_root_node.index_instance_nodes.create()

            index_instance = IndexInstance.objects.get(pk=self.pk)
            queryset = Document.valid.filter(
                document_type__in=self.document_types.all()
            )
            for document in queryset:
                index_instance.document_add(document=document)

    def reset(self):
        self.delete_index_instance_nodes()

        self.index_template_root_node.initialize_index_instance_root_node()


class IndexTemplateNodeBusinessLogicMixin:
    def get_index_instance_root_node(self):
        return self.index_instance_nodes.get(parent=None)

    def initialize_index_instance_root_node(self):
        index_instance_root_node, created = self.index_instance_nodes.get_or_create(
            parent=None
        )

        return index_instance_root_node
