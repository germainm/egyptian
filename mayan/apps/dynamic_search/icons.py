from mayan.apps.icons.icons import Icon

icon_result_list = Icon(driver_name='fontawesome', symbol='magnifying-glass')

icon_saved_resultset_delete_single = Icon(
    driver_name='fontawesome', symbol='trash-can'
)
icon_saved_resultset_list = Icon(
    driver_name='fontawesome', symbol='bookmark'
)
icon_saved_resultset_result_list = Icon(
    driver_name='fontawesome', symbol='bookmark'
)

icon_search = Icon(driver_name='fontawesome', symbol='magnifying-glass')
icon_search_advanced = Icon(driver_name='fontawesome', symbol='magnifying-glass-plus')
icon_search_again = Icon(driver_name='fontawesome', symbol='arrows-rotate')
icon_search_backend_reindex = Icon(
    driver_name='fontawesome-layers', data=[
        {
            'class': 'fa-solid fa-circle',
            'transform': 'down-3 right-10',
            'mask': 'fa-solid fa-magnifying-glass'
        },
        {'class': 'fa-regular fa-circle', 'transform': 'down-3 right-10'},
        {'class': 'fa-solid fa-magnifying-glass', 'transform': 'flip-h left-3'},
        {'class': 'fa-solid fa-hammer', 'transform': 'shrink-4 down-3 right-10'}
    ]
)
icon_search_form_clear = Icon(
    driver_name='fontawesome', symbol='circle-xmark'
)
icon_search_model_detail = Icon(
    driver_name='fontawesome', symbol='magnifying-glass-chart'
)
icon_search_model_list = Icon(
    driver_name='fontawesome', symbol='magnifying-glass-chart'
)
icon_search_submit = Icon(driver_name='fontawesome', symbol='magnifying-glass')
