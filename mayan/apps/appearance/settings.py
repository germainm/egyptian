from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .literals import (
    DEFAULT_APPEARANCE_APP_TEMPLATE_CACHE_VERIFY,
    DEFAULT_APPEARANCE_DATE_TIME_RELATIVE_ENABLE,
    DEFAULT_APPEARANCE_THEME,
    DEFAULT_APPEARANCE_THEME_USER_SELECTION_ENABLED,
    DEFAULT_APPEARANCE_ELIDED_PAGER_ON_EACH_SIDE,
    DEFAULT_APPEARANCE_ELIDED_PAGER_ON_ENDS,
    DEFAULT_APPEARANCE_PAGINATION_DROPDOWN_RANGE,
    DEFAULT_APPEARANCE_PAGINATION_DROPDOWN_ENABLE,
    DEFAULT_APPEARANCE_PAGINATION_INPUT_ENABLE,
    DEFAULT_MAXIMUM_TITLE_LENGTH,
    DEFAULT_MENU_POLLING_INTERVAL, DEFAULT_MESSAGE_POSITION,
    DEFAULT_THROTTLING_MAXIMUM_REQUESTS, DEFAULT_THROTTLING_TIMEOUT
)

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='Appearance'), name='appearance'
)

setting_app_template_cache_verify = setting_namespace.do_setting_add(
    data_type=bool, default=DEFAULT_APPEARANCE_APP_TEMPLATE_CACHE_VERIFY,
    global_name='APPEARANCE_APP_TEMPLATE_CACHE_VERIFY', help_text=_(
        message='Render every app template served from the app template '
        'cache a second time and raise an error when the two results differ. '
        'Used to detect app templates whose output varies per request and '
        'that are therefore not safe to cache. Enable only for testing, it '
        'renders every app template twice.'
    )
)
setting_date_time_relative_enable = setting_namespace.do_setting_add(
    data_type=bool,
    default=DEFAULT_APPEARANCE_DATE_TIME_RELATIVE_ENABLE,
    global_name='APPEARANCE_DATE_TIME_RELATIVE_ENABLE', help_text=_(
        message='Display date and time list columns as an amount of time '
        'relative to the present moment. The complete date and time is '
        'shown as a tooltip. Disable to display the complete date and time '
        'at all times.'
    )
)
setting_elided_pager_on_each_side = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_APPEARANCE_ELIDED_PAGER_ON_EACH_SIDE,
    global_name='APPEARANCE_ELIDED_PAGER_ON_EACH_SIDE', help_text=_(
        message='Number of pages to show on each side of the current '
        'page in the elided pager.'
    )
)
setting_elided_pager_on_ends = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_APPEARANCE_ELIDED_PAGER_ON_ENDS,
    global_name='APPEARANCE_ELIDED_PAGER_ON_ENDS', help_text=_(
        message='Number of pages to show at both ends of the elided pager.'
    )
)
setting_max_title_length = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_MAXIMUM_TITLE_LENGTH,
    global_name='APPEARANCE_MAXIMUM_TITLE_LENGTH', help_text=_(
        message='Maximum number of characters that will be displayed as the '
        'view title.'
    )
)
setting_message_position = setting_namespace.do_setting_add(
    choices=(
        'top-left', 'top-center', 'top-right', 'bottom-left',
        'bottom-center', 'bottom-right',
    ), default=DEFAULT_MESSAGE_POSITION,
    global_name='APPEARANCE_MESSAGE_POSITION', help_text=_(
        message='Position where the system messages will be displayed.'
    )
)
setting_menu_polling_interval = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_MENU_POLLING_INTERVAL,
    global_name='APPEARANCE_MENU_POLLING_INTERVAL', help_text=_(
        message='Delay in milliseconds after which the menus will be checked '
        'for updates.'
    )
)
setting_pagination_dropdown_enable = setting_namespace.do_setting_add(
    default=DEFAULT_APPEARANCE_PAGINATION_DROPDOWN_ENABLE,
    global_name='APPEARANCE_PAGINATION_DROPDOWN_ENABLE', help_text=_(
        message='Enable page selection dropdown.'
    )
)
setting_pagination_dropdown_range = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_APPEARANCE_PAGINATION_DROPDOWN_RANGE,
    global_name='APPEARANCE_PAGINATION_DROPDOWN_RANGE', help_text=_(
        message='Total pages to show in the page selection dropdown.'
    )
)
setting_pagination_input_enable = setting_namespace.do_setting_add(
    default=DEFAULT_APPEARANCE_PAGINATION_INPUT_ENABLE,
    global_name='APPEARANCE_PAGINATION_INPUT_ENABLE', help_text=_(
        message='Enable the page selection input field.'
    )
)
setting_theme = setting_namespace.do_setting_add(
    default=DEFAULT_APPEARANCE_THEME, global_name='APPEARANCE_THEME',
    help_text=_(
        message='Name of the theme (frontend stylesheet) used as the system '
        'default. When left unset the frontend\'s own default theme is used.'
    )
)
setting_theme_user_selection_enabled = setting_namespace.do_setting_add(
    data_type=bool,
    default=DEFAULT_APPEARANCE_THEME_USER_SELECTION_ENABLED,
    global_name='APPEARANCE_THEME_USER_SELECTION_ENABLED', help_text=_(
        message='Allow users to select their own theme. Disable to enforce '
        'the system default theme for every user.'
    )
)
setting_throttling_maximum_requests = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_THROTTLING_MAXIMUM_REQUESTS,
    global_name='APPEARANCE_THROTTLING_MAXIMUM_REQUESTS', help_text=_(
        message='Maximum number of requests that can be made before '
        'throttling is enabled.'
    )
)
setting_throttling_timeout = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_THROTTLING_TIMEOUT,
    global_name='APPEARANCE_THROTTLING_TIMEOUT', help_text=_(
        message='Time in milliseconds after which a throttled request will '
        'clear allowing an additional request to be performed.'
    )
)
