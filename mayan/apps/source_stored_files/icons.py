from mayan.apps.icons.icons import Icon

icon_error_staging_file = Icon(
    driver_name='fontawesome-layers', data=[
        {'class': 'fa-regular fa-file text-body'},
        {'class': 'fa-solid fa-image', 'transform': 'shrink-10 down-1'},
        {
            'class': 'fa-solid fa-ban text-danger', 'transform': 'shrink-7 down-1'
        }
    ]
)
icon_error_staging_file_too_large = Icon(
    driver_name='fontawesome-layers', data=[
        {'class': 'fa-regular fa-file text-body'},
        {'class': 'fa-solid fa-image', 'transform': 'shrink-10 down-1'},
        {
            'class': 'fa-solid fa-ban text-danger', 'transform': 'shrink-7 down-1'
        }
    ]
)

icon_storage_file_delete = Icon(driver_name='fontawesome', symbol='trash-can')
icon_storage_file_select = Icon(driver_name='fontawesome', symbol='check')
