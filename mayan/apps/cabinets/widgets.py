def jstree_data(node, selected_node):
    result = {
        'data': {
            'href': node.get_absolute_url()
        },
        'state': {
            'opened': True,
            'selected': node == selected_node
        },
        'text': node.label
    }

    children = node.get_children().order_by('label')

    if children:
        result['children'] = [
            jstree_data(node=child, selected_node=selected_node)
            for child in children
        ]

    return result
