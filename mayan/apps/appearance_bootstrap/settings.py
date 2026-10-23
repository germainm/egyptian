from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .literals import (
    DEFAULT_APPEARANCE_BOOTSTRAP_CARD_LABEL_LINE_COUNT_MAXIMUM,
    DEFAULT_APPEARANCE_BOOTSTRAP_COLOR_MODE,
    DEFAULT_APPEARANCE_BOOTSTRAP_COLOR_MODE_USER_SELECTION_ENABLED
)

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='Appearance (Bootstrap)'), name='appearance_bootstrap'
)

setting_color_mode = setting_namespace.do_setting_add(
    default=DEFAULT_APPEARANCE_BOOTSTRAP_COLOR_MODE,
    global_name='APPEARANCE_BOOTSTRAP_COLOR_MODE', help_text=_(
        message='Name of the color mode (e.g. `light` or `dark`) used as the '
        'system default. When left unset the frontend\'s own default color '
        'mode is used.'
    )
)
setting_color_mode_user_selection_enabled = setting_namespace.do_setting_add(
    data_type=bool,
    default=DEFAULT_APPEARANCE_BOOTSTRAP_COLOR_MODE_USER_SELECTION_ENABLED,
    global_name='APPEARANCE_BOOTSTRAP_COLOR_MODE_USER_SELECTION_ENABLED',
    help_text=_(
        message='Allow users to select their own color mode. Disable to '
        'enforce the system default color mode for every user.'
    )
)
setting_card_label_line_count_maximum = setting_namespace.do_setting_add(
    data_type=int,
    default=DEFAULT_APPEARANCE_BOOTSTRAP_CARD_LABEL_LINE_COUNT_MAXIMUM,
    global_name='APPEARANCE_BOOTSTRAP_CARD_LABEL_LINE_COUNT_MAXIMUM',
    help_text=_(
        message='Maximum number of text lines the label of a list card is '
        'allowed to occupy. Labels longer than this are truncated and the '
        'complete label is shown as a tooltip. Use 0 to disable truncation '
        'and allow the label to occupy as many lines as needed.'
    )
)
