from django.template.loader import render_to_string

from .icons import (
    icon_index, icon_index_instance_node_with_documents, icon_index_level_up
)


def node_tree(node, user):
    ancestor_list = list(
        node.get_ancestors(include_self=True)
    )
    ancestor_count = len(ancestor_list)

    item_list = []

    for ancestor in ancestor_list:
        if ancestor.is_root_node():
            element = node.index()
            icon = icon_index
        else:
            element = ancestor
            if element.index_template_node.link_documents:
                icon = icon_index_instance_node_with_documents
            else:
                icon = icon_index_level_up

        item_list.append(
            {
                'active': element == node or ancestor_count == 1,
                'count': element.get_descendants_document_count(user=user),
                'icon': icon,
                'text': element,
                'url': element.get_absolute_url()
            }
        )

    return render_to_string(
        context={'item_list': item_list},
        template_name='document_indexing/widgets/index_instance_node_tree.html'
    )
