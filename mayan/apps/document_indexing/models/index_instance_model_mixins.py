import logging
from contextlib import contextmanager
from functools import lru_cache

from django.apps import apps
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.models import AccessControlList
from mayan.apps.documents.models.document_models import Document
from mayan.apps.documents.permissions import permission_document_view
from mayan.apps.lock_manager.backends.base import LockingBackend
from mayan.apps.templating.template_backends import Template

logger = logging.getLogger(name=__name__)


class IndexInstanceBusinessLogicMixin:
    @staticmethod
    @lru_cache(maxsize=1)
    def _get_index_instance_node_value_max_length():
        IndexInstanceNode = apps.get_model(
            app_label='document_indexing', model_name='IndexInstanceNode'
        )
        field = IndexInstanceNode._meta.get_field(field_name='value')

        return field.max_length

    def _delete_empty_nodes(self, index_instance_root_node=None):
        IndexInstanceNode = apps.get_model(
            app_label='document_indexing', model_name='IndexInstanceNode'
        )

        if index_instance_root_node is None:
            index_instance_root_node = self.index_instance_root_node

        while True:
            pk_list = list(
                index_instance_root_node.get_descendants().filter(
                    children=None, documents=None
                ).values_list('pk', flat=True).distinct()
            )

            if not pk_list:
                break

            IndexInstanceNode.objects.filter(pk__in=pk_list).delete()

    def _get_index_template_node_children_map(self):
        try:
            return self._index_template_node_children_map
        except AttributeError:
            IndexTemplateNode = apps.get_model(
                app_label='document_indexing', model_name='IndexTemplateNode'
            )

            children_map = {}
            for index_template_node in IndexTemplateNode.objects.filter(
                enabled=True, index=self.pk
            ):
                children_map.setdefault(
                    index_template_node.parent_id, []
                ).append(index_template_node)

            self._index_template_node_children_map = children_map

            return children_map

    def _document_add(
        self, document, index_instance_node_parent, index_template_node_parent
    ):
        children_map = self._get_index_template_node_children_map()
        value_max_length = IndexInstanceBusinessLogicMixin._get_index_instance_node_value_max_length()

        for index_template_node in children_map.get(index_template_node_parent.pk, ()):
            try:
                template = Template(
                    template_string=index_template_node.expression
                )
                result = template.render(
                    context={'document': document}
                )
            except Exception as exception:
                logger.error('Evaluating error: %s', exception)
                error_message = _(
                    message='Error indexing document: %(document)s; '
                    'expression: %(expression)s; %(exception)s'
                ) % {
                    'document': document,
                    'exception': exception,
                    'expression': index_template_node.expression
                }
                logger.debug(msg=error_message)
            else:
                logger.debug('Evaluation result: %s', result)

                if result:
                    index_instance_node, created = index_template_node.index_instance_nodes.get_or_create(
                        parent=index_instance_node_parent,
                        value=result[:value_max_length]
                    )

                    if index_template_node.link_documents:
                        index_instance_node.documents.add(document)

                    self._document_add(
                        document=document,
                        index_instance_node_parent=index_instance_node,
                        index_template_node_parent=index_template_node
                    )

    @contextmanager
    def _acquire_lock(self, name):
        locking_backend = LockingBackend.get_backend()
        lock = locking_backend.acquire_lock(name=name)
        try:
            yield lock
        finally:
            lock.release()

    def delete_empty_nodes(self):
        if not self.enabled:
            return

        lock_name = self.get_lock_string()
        with self._acquire_lock(name=lock_name):
            self.initialize_index_instance_root_node_node()
            self._delete_empty_nodes()

    def document_nodes_delete(self, document):
        IndexInstanceNode = apps.get_model(
            app_label='document_indexing', model_name='IndexInstanceNode'
        )

        deleted_count, deleted_detail = IndexInstanceNode.documents.through.objects.filter(
            document=document,
            indexinstancenode__index_template_node__enabled=True,
            indexinstancenode__index_template_node__index=self
        ).delete()

        return deleted_count

    def document_add(self, document):
        logger.debug('Index; Indexing document: %s', document)

        if Document.valid.filter(pk=document.pk).exists() and self.enabled and self.document_types.filter(pk=document.document_type.pk).exists():
            lock_name_index = self.get_lock_string()
            lock_name_document = self.get_document_lock_string(
                document=document
            )
            with self._acquire_lock(name=lock_name_index), self._acquire_lock(name=lock_name_document):
                with transaction.atomic():
                    index_instance_root_node = self.initialize_index_instance_root_node_node()

                    deleted_count = self.document_nodes_delete(
                        document=document
                    )

                    self._document_add(
                        document=document,
                        index_instance_node_parent=index_instance_root_node,
                        index_template_node_parent=self.index_template_root_node
                    )

                    if deleted_count:
                        self._delete_empty_nodes(
                            index_instance_root_node=index_instance_root_node
                        )

    def document_remove(self, document):
        if self.enabled and self.document_types.filter(pk=document.document_type.pk).exists():
            lock_name_index = self.get_lock_string()
            lock_name_document = self.get_document_lock_string(
                document=document
            )
            with self._acquire_lock(name=lock_name_index), self._acquire_lock(name=lock_name_document):
                deleted_count = self.document_nodes_delete(document=document)

                if deleted_count:
                    self._delete_empty_nodes()

    def get_children(self):
        return self.index_instance_root_node.get_children()

    def get_document_lock_string(self, document):
        return 'indexing:document_{}'.format(document.pk)

    def get_descendants(self):
        return self.index_instance_root_node.get_descendants()

    def get_descendants_count(self):
        return self.index_instance_root_node.get_descendants_count()

    get_descendants_count.help_text = _(
        message='Total number of nodes with unique values this item contains.'
    )

    def get_descendants_document_count(self, user):
        return self.index_instance_root_node.get_descendants_document_count(
            user=user
        )

    get_descendants_document_count.help_text = _(
        message='Total number of unique documents this item contains.'
    )

    def get_lock_string(self):
        return 'indexing:index_instance_{}'.format(self.pk)

    def get_level_count(self):
        return self.index_instance_root_node.get_level_count()

    get_level_count.help_text = _(
        message='Total number of node levels this item contains.'
    )

    def get_root(self):
        return self.index_instance_root_node

    @property
    def index_instance_root_node(self):
        return self.index_template_root_node.get_index_instance_root_node()

    def initialize_index_instance_root_node_node(self):
        return self.index_template_root_node.initialize_index_instance_root_node()


class IndexInstanceNodeBusinessLogicMixin:
    def _get_documents(self):
        return Document.valid.filter(
            pk__in=self.documents.values('pk')
        )

    def get_children_count(self):
        return self.get_children().count()

    def get_descendants_count(self):
        return self.get_descendants().count()

    get_descendants_count.help_text = IndexInstanceBusinessLogicMixin.get_descendants_count.help_text

    def get_descendants_document_count(self, user):
        queryset = Document.valid.filter(
            index_instance_nodes__in=self.get_descendants(
                include_self=True
            )
        ).distinct()

        return AccessControlList.objects.restrict_queryset(
            permission=permission_document_view,
            queryset=queryset, user=user
        ).count()

    get_descendants_document_count.help_text = IndexInstanceBusinessLogicMixin.get_descendants_document_count.help_text

    def get_documents(self, permission, user):
        return AccessControlList.objects.restrict_queryset(
            permission=permission, queryset=self._get_documents(),
            user=user
        )

    def get_full_path(self):
        result = []
        for node in self.get_ancestors(include_self=True):
            if node.is_root_node():
                result.append(
                    str(
                        self.index()
                    )
                )
            else:
                result.append(
                    str(node)
                )

        return ' / '.join(result)
    get_full_path.help_text = _(
        message='The path to the index including all ancestors.'
    )
    get_full_path.short_description = _(message='Full path')

    def get_level_count(self):
        return self.get_descendants().values('level').distinct().count()

    get_level_count.help_text = IndexInstanceBusinessLogicMixin.get_level_count.help_text

    def index(self):
        try:
            return self._index_instance
        except AttributeError:
            IndexInstance = apps.get_model(
                app_label='document_indexing', model_name='IndexInstance'
            )

            self._index_instance = IndexInstance.objects.get(
                pk=self.index_template_node.index.pk
            )

            return self._index_instance
