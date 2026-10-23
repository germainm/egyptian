from mayan.apps.icons.icons import Icon

icon_ajax_refresh = Icon(
    driver_name='fontawesome', symbol='arrows-rotate'
)

icon_error_400 = Icon(
    driver_name='fontawesome-layers', data=[
        {'class': 'fa-solid fa-display'},
        {'class': 'fa-solid fa-ban', 'transform': 'shrink-8 up-2'}
    ]
)
icon_error_403 = Icon(
    driver_name='fontawesome-layers', data=[
        {'class': 'fa-solid fa-display'},
        {'class': 'fa-solid fa-lock', 'transform': 'shrink-8 up-2'}
    ]
)
icon_error_403_csrf = Icon(
    driver_name='fontawesome-layers', data=[
        {'class': 'fa-solid fa-display'},
        {'class': 'fa-solid fa-hourglass-end', 'transform': 'shrink-8 up-2'}
    ]
)
icon_error_404 = Icon(
    driver_name='fontawesome-layers', data=[
        {'class': 'fa-solid fa-display'},
        {'class': 'fa-solid fa-question', 'transform': 'shrink-8 up-2'}
    ]
)
icon_error_500 = Icon(
    driver_name='fontawesome-layers', data=[
        {'class': 'fa-solid fa-display'},
        {'class': 'fa-solid fa-triangle-exclamation', 'transform': 'shrink-8 up-2'}
    ]
)

icon_error_403_csrf_hint_reload = Icon(
    driver_name='fontawesome', symbol='arrows-rotate'
)
icon_error_403_csrf_hint_cookies = Icon(
    driver_name='fontawesome', symbol='cookie-bite'
)
icon_error_403_csrf_hint_login = Icon(
    driver_name='fontawesome', symbol='right-to-bracket'
)

icon_error_404_hint_location_invalid = Icon(
    driver_name='fontawesome', symbol='question'
)
icon_error_404_hint_object_deleted = Icon(
    driver_name='fontawesome', symbol='trash-can'
)
icon_error_404_hint_permission = Icon(
    driver_name='fontawesome', symbol='lock'
)

icon_error_500_hint_administrator = Icon(
    driver_name='fontawesome', symbol='phone'
)
icon_error_500_hint_issue_tracker = Icon(
    driver_name='fontawesome', symbol='bug'
)
icon_error_500_hint_logs = Icon(
    driver_name='fontawesome', symbol='scroll'
)
icon_error_500_hint_refresh = Icon(
    driver_name='fontawesome', symbol='arrows-rotate'
)
icon_error_500_hint_wait = Icon(
    driver_name='fontawesome', style='fa-regular', symbol='hourglass'
)

icon_menu_actions = Icon(driver_name='fontawesome', symbol='ellipsis-vertical')
icon_menu_topbar = Icon(driver_name='fontawesome', symbol='gear')
icon_menu_views = Icon(driver_name='fontawesome', symbol='eye')
icon_no_results = Icon(driver_name='fontawesome', symbol='xmark')
icon_theme = Icon(driver_name='fontawesome', symbol='palette')
