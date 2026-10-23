from django.utils.translation import gettext_lazy as _

from mayan.apps.smart_settings.setting_clusters import setting_cluster

from .literals import (
    DEFAULT_FORMS_COLOR_AUTO_ENABLED,
    DEFAULT_FORMS_DROPZONE_PARALLEL_UPLOADS,
    DEFAULT_FORMS_SHOW_DROPZONE_SUBMIT_BUTTON
)

setting_namespace = setting_cluster.do_namespace_add(
    label=_(message='Forms'), name='forms'
)

setting_color_auto_enabled = setting_namespace.do_setting_add(
    default=DEFAULT_FORMS_COLOR_AUTO_ENABLED,
    global_name='FORMS_COLOR_AUTO_ENABLED', help_text=_(
        message='Calculate the color of a color field from the text of '
        'another field of the same form, while that text is typed. Applies '
        'to the form of a new object and to the form of an object that '
        'already has a color; an object keeps its color until its text is '
        'edited. The calculated color is replaced by selecting a color, and '
        'the button of the color field turns the calculation on and off.'
    )
)

setting_dropzone_parallel_uploads = setting_namespace.do_setting_add(
    data_type=int, default=DEFAULT_FORMS_DROPZONE_PARALLEL_UPLOADS,
    global_name='FORMS_DROPZONE_PARALLEL_UPLOADS', help_text=_(
        message='Number of files that will be uploaded at the same time by '
        'the dropzone widget.'
    )
)

setting_show_dropzone_submit_button = setting_namespace.do_setting_add(
    default=DEFAULT_FORMS_SHOW_DROPZONE_SUBMIT_BUTTON,
    global_name='FORMS_SHOW_DROPZONE_SUBMIT_BUTTON', help_text=_(
        message='Display a submit button and wait for the submit button to be '
        'pressed before processing up the upload.'
    )
)
