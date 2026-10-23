from django.utils.translation import gettext_lazy as _

from mayan.apps.navigation.links import Link
from mayan.apps.navigation.utils import factory_condition_queryset_access

from .icons import (
    icon_document_index_instance_list, icon_document_type_index_templates,
    icon_index, icon_index_instances_rebuild, icon_index_instances_reset,
    icon_index_template_create, icon_index_template_delete,
    icon_index_template_document_types, icon_index_template_edit,
    icon_index_template_event_triggers, icon_index_template_list,
    icon_index_template_node_create, icon_index_template_node_delete,
    icon_index_template_node_edit, icon_index_template_node_tree_view
)
from .permissions import (
    permission_index_instance_view, permission_index_template_create,
    permission_index_template_delete, permission_index_template_edit,
    permission_index_template_rebuild, permission_index_template_view
)


def condition_is_not_root_node(context, resolved_object):
    return not resolved_object.is_root_node()



link_document_index_instance_list = Link(
    args='resolved_object.pk', icon=icon_document_index_instance_list,
    permission=permission_index_instance_view,
    text=_(message='Indexes'), view='indexing:document_index_list'
)

link_document_type_index_templates = Link(
    args='resolved_object.pk', icon=icon_document_type_index_templates,
    permission=permission_index_template_create,
    text=_(message='Index templates'), view='indexing:document_type_index_templates'
)


link_index_instance_menu = Link(
    condition=factory_condition_queryset_access(
        app_label='document_indexing', model_name='IndexTemplate',
        object_permission=permission_index_instance_view,
    ), icon=icon_index,
    text=_(message='Indexes'), view='indexing:index_list'
)
link_index_instance_rebuild = Link(
    args='resolved_object.pk', icon=icon_index_instances_rebuild,
    permission=permission_index_template_rebuild,
    text=_(message='Rebuild index'), view='indexing:index_template_rebuild'
)
link_index_instances_rebuild = Link(
    condition=factory_condition_queryset_access(
        app_label='document_indexing', model_name='IndexTemplate',
        object_permission=permission_index_template_rebuild,
    ), description=_(
        message='Deletes and creates from scratch all the document indexes.'
    ), icon=icon_index_instances_rebuild, text=_(message='Rebuild indexes'),
    view='indexing:rebuild_index_instances'
)
link_index_instances_reset = Link(
    condition=factory_condition_queryset_access(
        app_label='document_indexing', model_name='IndexTemplate',
        object_permission=permission_index_template_rebuild,
    ), description=_(
        message='Deletes and creates from scratch all the document indexes.'
    ), icon=icon_index_instances_reset, text=_(message='Reset indexes'),
    view='indexing:index_instances_reset'
)


link_index_template_create = Link(
    icon=icon_index_template_create,
    permission=permission_index_template_create,
    text=_(message='Create index'), view='indexing:index_template_create'
)
link_index_template_delete = Link(
    args='resolved_object.pk', icon=icon_index_template_delete,
    permission=permission_index_template_delete, tags='dangerous',
    text=_(message='Delete'), view='indexing:index_template_delete',
)
link_index_template_document_types = Link(
    args='resolved_object.pk', icon=icon_index_template_document_types,
    permission=permission_index_template_edit,
    text=_(message='Document types'), view='indexing:index_template_document_types'
)
link_index_template_edit = Link(
    args='resolved_object.pk', icon=icon_index_template_edit,
    permission=permission_index_template_edit, text=_(message='Edit'),
    view='indexing:index_template_edit'
)
link_index_template_event_triggers = Link(
    args='resolved_object.pk', icon=icon_index_template_event_triggers,
    permission=permission_index_template_edit, text=_(message='Triggers'),
    view='indexing:index_template_event_triggers'
)
link_index_template_list = Link(
    icon=icon_index_template_list, text=_(message='Index templates'),
    view='indexing:index_template_list'
)
link_index_template_setup = Link(
    condition=factory_condition_queryset_access(
        app_label='document_indexing', model_name='IndexTemplate',
        object_permission=permission_index_template_view,
        view_permission=permission_index_template_create,
    ), icon=icon_index, text=_(message='Indexes'),
    view='indexing:index_template_list'
)


link_index_template_node_tree_view = Link(
    args='resolved_object.pk', icon=icon_index_template_node_tree_view,
    permission=permission_index_template_edit, text=_(message='Tree template'),
    view='indexing:index_template_view'
)
link_index_template_node_create = Link(
    args='resolved_object.pk', icon=icon_index_template_node_create,
    text=_(message='New child node'), view='indexing:template_node_create'
)
link_index_template_node_delete = Link(
    args='resolved_object.pk', condition=condition_is_not_root_node,
    icon=icon_index_template_node_delete, tags='dangerous',
    text=_(message='Delete'), view='indexing:template_node_delete'
)
link_index_template_node_edit = Link(
    args='resolved_object.pk', icon=icon_index_template_node_edit,
    condition=condition_is_not_root_node, text=_(message='Edit'),
    view='indexing:template_node_edit'
)
