from mayan.apps.icons.icons import Icon

icon_thumbnail_image_loading = Icon(
    css_classes='fa-spin', driver_name='fontawesome', style='fa-regular',
    symbol='clock'
)

icon_error_broken_file = Icon(
    driver_name='fontawesome-layers', data=[
        {'class': 'fa-regular fa-file text-body'},
        {'class': 'fa-solid fa-image', 'transform': 'shrink-10 down-1'},
        {
            'class': 'fa-solid fa-slash text-danger',
            'transform': 'shrink-7 down-1'
        }
    ]
)
icon_error_image_busy = Icon(
    driver_name='fontawesome-layers', data=[
        {'class': 'fa-regular fa-file text-body'},
        {'class': 'fa-solid fa-image', 'transform': 'shrink-10 down-1'},
        {
            'class': 'fa-solid fa-gear text-info',
            'transform': 'shrink-7 down-1'
        }
    ]
)
icon_error_request_throttled = Icon(
    driver_name='fontawesome-layers', data=[
        {'class': 'fa-regular fa-file text-body'},
        {'class': 'fa-solid fa-image', 'transform': 'shrink-10 down-1'},
        {
            'class': 'fa-solid fa-hourglass-half text-warning',
            'transform': 'shrink-7 down-1'
        }
    ]
)
icon_error_unexpected = Icon(
    driver_name='fontawesome-layers', data=[
        {'class': 'fa-regular fa-file text-body'},
        {
            'class': 'fa-solid fa-triangle-exclamation text-danger',
            'transform': 'shrink-7 down-1'
        }
    ]
)

icon_asset_create = Icon(driver_name='fontawesome', symbol='image')
icon_asset_delete_multiple = Icon(driver_name='fontawesome', symbol='trash-can')
icon_asset_delete_single = icon_asset_delete_multiple
icon_asset_detail = Icon(driver_name='fontawesome', symbol='image')
icon_asset_edit = Icon(driver_name='fontawesome', symbol='pencil')
icon_asset_list = Icon(driver_name='fontawesome', symbol='image')

icon_transformations = Icon(driver_name='fontawesome', symbol='crop')

icon_transformation_create = Icon(driver_name='fontawesome', symbol='plus')
icon_transformation_delete = Icon(driver_name='fontawesome', symbol='trash-can')
icon_transformation_edit = Icon(
    driver_name='fontawesome', symbol='pencil'
)
icon_transformation_list = icon_transformations
icon_transformation_select = Icon(driver_name='fontawesome', symbol='plus')

icon_layer_decorations = Icon(
    driver_name='fontawesome', symbol='paint-roller'
)
icon_layer_transformation = Icon(
    driver_name='fontawesome', symbol='crop'
)
