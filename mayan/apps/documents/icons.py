from mayan.apps.converter.icons import icon_transformations
from mayan.apps.icons.icons import Icon


icon_document = Icon(driver_name='fontawesome', symbol='book')
icon_menu_documents = Icon(driver_name='fontawesome', symbol='book')


icon_dashboard_documents_in_trash = Icon(
    driver_name='fontawesome', symbol='trash-can'
)
icon_dashboard_pages_per_month = Icon(
    driver_name='fontawesome', symbol='copy'
)
icon_dashboard_new_documents_this_month = Icon(
    driver_name='fontawesome', symbol='calendar'
)
icon_dashboard_total_document = Icon(
    driver_name='fontawesome', symbol='book'
)


icon_error_document_file_has_no_pages = Icon(
    driver_name='fontawesome-layers', data=[
        {'class': 'fa-regular fa-file text-body'},
        {'class': 'fa-solid fa-copy', 'transform': 'shrink-10 down-2'},
        {'class': 'fa-solid fa-ban text-danger', 'transform': 'shrink-7 down-2'}
    ]
)
icon_error_document_file_page_transformation = Icon(
    driver_name='fontawesome-layers', data=[
        {'class': 'fa-regular fa-file text-body'},
        {'class': 'fa-solid fa-crop', 'transform': 'shrink-11  down-2'},
        {
            'class': 'fa-solid fa-exclamation text-danger',
            'transform': 'shrink-11 down-2'
        }
    ]
)
icon_error_document_version_page_transformation = Icon(
    driver_name='fontawesome-layers', data=[
        {'class': 'fa-regular fa-file text-body'},
        {'class': 'fa-solid fa-crop', 'transform': 'shrink-11 down-1'},
        {
            'class': 'fa-solid fa-exclamation text-danger',
            'transform': 'shrink-11 down-2'
        }
    ]
)
icon_error_no_valid_version = Icon(
    driver_name='fontawesome-layers', data=[
        {'class': 'fa-regular fa-file text-body'},
        {'class': 'fa-solid fa-code-branch', 'transform': 'shrink-10 down-2'},
        {'class': 'fa-solid fa-ban text-danger', 'transform': 'shrink-7 down-2'}
    ]
)
icon_error_no_version_pages = Icon(
    driver_name='fontawesome-layers', data=[
        {'class': 'fa-regular fa-file text-body'},
        {'class': 'fa-solid fa-code-branch', 'transform': 'shrink-10 down-1'},
        {'class': 'fa-solid fa-ban text-danger', 'transform': 'shrink-7 down-1'}
    ]
)


icon_document_image_loading = Icon(
    css_classes='fa-spin', driver_name='fontawesome', style='fa-regular',
    symbol='clock'
)
icon_document_return = Icon(
    driver_name='fontawesome-dual', primary_symbol='book',
    secondary_symbol='chevron-left'
)


icon_document_type = Icon(
    driver_name='fontawesome-layers', data=[
        {'class': 'fa-solid fa-circle', 'transform': 'shrink-12 up-2'},
        {
            'class': 'fa-solid fa-gear', 'transform': 'shrink-6 up-2',
            'mask': 'fa-solid fa-book'
        }
    ]
)

icon_dashboard_document_types = icon_document_type
icon_document_type_create = Icon(
    driver_name='fontawesome-dual', primary_symbol='book',
    secondary_symbol='plus'
)
icon_document_type_delete = Icon(driver_name='fontawesome', symbol='trash-can')
icon_document_type_document_list = Icon(
    driver_name='fontawesome', symbol='book'
)
icon_document_type_edit = Icon(driver_name='fontawesome', symbol='pencil')
icon_document_type_setup = icon_document_type

icon_document_type_list = icon_document_type

icon_document_type_filename = Icon(
    driver_name='fontawesome', symbol='keyboard'
)
icon_document_type_filename_create = Icon(
    driver_name='fontawesome-dual', primary_symbol='keyboard',
    secondary_symbol='plus'
)
icon_document_type_filename_delete = Icon(
    driver_name='fontawesome', symbol='trash-can'
)
icon_document_type_filename_edit = Icon(
    driver_name='fontawesome', symbol='pencil'
)
icon_document_type_filename_list = Icon(
    driver_name='fontawesome', symbol='keyboard'
)

icon_document_type_filename_generator = Icon(
    driver_name='fontawesome-layers', data=[
        {'class': 'fa-regular fa-file'},
        {'class': 'fa-solid fa-gear', 'transform': 'shrink-8 down-2'}
    ]
)

icon_document_type_retention_policies = Icon(
    driver_name='fontawesome', symbol='clock'
)
icon_document_type_setup = icon_document_type


icon_document_list = Icon(driver_name='fontawesome', symbol='book')
icon_document_preview = Icon(driver_name='fontawesome', symbol='eye')
icon_document_properties_detail = Icon(
    driver_name='fontawesome', symbol='info'
)
icon_document_properties_edit = Icon(
    driver_name='fontawesome', symbol='pencil'
)
icon_document_trash_multiple = Icon(
    driver_name='fontawesome', symbol='trash-can'
)
icon_document_trash_single = icon_document_trash_multiple
icon_document_type_change_multiple = icon_document_type
icon_document_type_change_single = icon_document_type_change_multiple


icon_document_file_delete = Icon(
    driver_name='fontawesome', symbol='xmark'
)
icon_document_file_edit = Icon(
    driver_name='fontawesome', symbol='pencil'
)
icon_document_file_introspect = Icon(
    driver_name='fontawesome', symbol='microscope'
)
icon_document_file_list = Icon(
    driver_name='fontawesome', symbol='hard-drive'
)
icon_document_file_preview = Icon(
    driver_name='fontawesome', symbol='eye'
)
icon_document_file_print = Icon(
    driver_name='fontawesome', symbol='print'
)
icon_document_file_properties_detail = Icon(
    driver_name='fontawesome', symbol='info'
)
icon_document_file_return_to_document = icon_document_return
icon_document_file_return_list = Icon(
    driver_name='fontawesome-dual', primary_symbol='hard-drive',
    secondary_symbol='chevron-left'
)
icon_document_file_transformation_list_clear = Icon(
    driver_name='fontawesome-dual',
    primary_symbol=icon_transformations.kwargs['symbol'],
    secondary_symbol='xmark'
)
icon_document_file_transformation_list_clone = Icon(
    driver_name='fontawesome-dual',
    primary_symbol=icon_transformations.kwargs['symbol'],
    secondary_symbol='arrow-right'
)


icon_document_file_page_list = Icon(driver_name='fontawesome', symbol='copy')
icon_document_file_page_navigation_first = Icon(
    css_classes='mayan-icon-directional', driver_name='fontawesome',
    symbol='backward-step'
)
icon_document_file_page_navigation_last = Icon(
    css_classes='mayan-icon-directional', driver_name='fontawesome',
    symbol='forward-step'
)
icon_document_file_page_navigation_next = Icon(
    css_classes='mayan-icon-directional', driver_name='fontawesome',
    symbol='arrow-right'
)
icon_document_file_page_navigation_previous = Icon(
    css_classes='mayan-icon-directional', driver_name='fontawesome',
    symbol='arrow-left'
)
icon_document_file_page_return_to_document = icon_document_return
icon_document_file_page_return_to_document_file = Icon(
    driver_name='fontawesome-dual', primary_symbol='hard-drive',
    secondary_symbol='chevron-left'
)
icon_document_file_page_return_to_document_file_page_list = Icon(
    driver_name='fontawesome-dual', primary_symbol='copy',
    secondary_symbol='chevron-left'
)
icon_document_file_page_rotate_left = Icon(
    driver_name='fontawesome', symbol='arrow-rotate-left'
)
icon_document_file_page_rotate_right = Icon(
    driver_name='fontawesome', symbol='arrow-rotate-right'
)
icon_document_file_page_detail = Icon(
    driver_name='fontawesome', symbol='image'
)
icon_document_file_page_detail_reset = Icon(
    driver_name='fontawesome', symbol='arrows-rotate'
)
icon_document_file_page_zoom_in = Icon(
    driver_name='fontawesome', symbol='magnifying-glass-plus'
)
icon_document_file_page_zoom_out = Icon(
    driver_name='fontawesome', symbol='magnifying-glass-minus'
)


icon_document_version_active = Icon(
    driver_name='fontawesome', symbol='check'
)
icon_document_version_create = Icon(
    driver_name='fontawesome-dual', primary_symbol='code-branch',
    secondary_symbol='plus'
)
icon_document_version_delete_multiple = Icon(
    driver_name='fontawesome', symbol='xmark'
)
icon_document_version_delete_single = icon_document_version_delete_multiple
icon_document_version_edit = Icon(
    driver_name='fontawesome', symbol='pencil'
)
icon_document_version_list = Icon(
    driver_name='fontawesome', symbol='code-branch'
)
icon_document_version_modification = Icon(
    driver_name='fontawesome', symbol='wrench'
)
icon_document_version_return_document = icon_document_return
icon_document_version_return_list = Icon(
    driver_name='fontawesome-dual', primary_symbol='code-branch',
    secondary_symbol='chevron-left'
)
icon_document_version_preview = Icon(
    driver_name='fontawesome', symbol='eye'
)
icon_document_version_print = Icon(
    driver_name='fontawesome', symbol='print'
)
icon_document_version_transformation_clear_multiple = Icon(
    driver_name='fontawesome-dual',
    primary_symbol=icon_transformations.kwargs['symbol'],
    secondary_symbol='xmark'
)
icon_document_version_transformation_clear_single = icon_document_version_transformation_clear_multiple
icon_document_version_transformations_clone = Icon(
    driver_name='fontawesome-dual',
    primary_symbol=icon_transformations.kwargs['symbol'],
    secondary_symbol='arrow-right'
)


icon_document_version_page_delete = Icon(
    driver_name='fontawesome', symbol='xmark'
)
icon_document_version_page_return_to_document = icon_document_return
icon_document_version_page_return_to_document_version = Icon(
    driver_name='fontawesome-dual', primary_symbol='code-branch',
    secondary_symbol='chevron-left'
)
icon_document_version_page_return_to_document_version_page_list = Icon(
    driver_name='fontawesome-dual', primary_symbol='copy',
    secondary_symbol='chevron-left'
)
icon_document_version_page_list = Icon(
    driver_name='fontawesome', symbol='copy'
)
icon_document_version_page_list_remap = Icon(
    driver_name='fontawesome', symbol='diagram-project'
)
icon_document_version_page_navigation_first = Icon(
    css_classes='mayan-icon-directional', driver_name='fontawesome',
    symbol='backward-step'
)
icon_document_version_page_navigation_last = Icon(
    css_classes='mayan-icon-directional', driver_name='fontawesome',
    symbol='forward-step'
)
icon_document_version_page_navigation_next = Icon(
    css_classes='mayan-icon-directional', driver_name='fontawesome',
    symbol='arrow-right'
)
icon_document_version_page_navigation_previous = Icon(
    css_classes='mayan-icon-directional', driver_name='fontawesome',
    symbol='arrow-left'
)
icon_document_version_page_rotate_left = Icon(
    driver_name='fontawesome', symbol='arrow-rotate-left'
)
icon_document_version_page_rotate_right = Icon(
    driver_name='fontawesome', symbol='arrow-rotate-right'
)
icon_document_version_page_detail = Icon(
    driver_name='fontawesome', symbol='image'
)
icon_document_version_page_detail_reset = Icon(
    driver_name='fontawesome', symbol='arrows-rotate'
)
icon_document_version_page_zoom_in = Icon(
    driver_name='fontawesome', symbol='magnifying-glass-plus'
)
icon_document_version_page_zoom_out = Icon(
    driver_name='fontawesome', symbol='magnifying-glass-minus'
)


icon_document_recently_accessed_list = Icon(
    driver_name='fontawesome', symbol='clock'
)


icon_document_recently_created_list = Icon(
    driver_name='fontawesome', symbol='asterisk'
)


icon_trash_can_empty = Icon(
    driver_name='fontawesome-dual', primary_symbol='trash-can',
    secondary_symbol='minus'
)
icon_trashed_document_delete_multiple = Icon(
    driver_name='fontawesome', symbol='xmark'
)
icon_trashed_document_delete_single = icon_trashed_document_delete_multiple
icon_trashed_document_list = Icon(
    driver_name='fontawesome', symbol='trash-can'
)
icon_trashed_document_restore_multiple = Icon(
    driver_name='fontawesome', symbol='recycle'
)
icon_trashed_document_restore_single = icon_trashed_document_restore_multiple
