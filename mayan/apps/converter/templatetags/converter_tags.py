import json

from django.template import Library
from django.utils.safestring import mark_safe

from mayan.apps.rest_api.literals import THROTTLING_PERIOD_MULTIPLIER_MAP
from mayan.apps.rest_api.settings import (
    setting_throttling_enabled, setting_throttling_rate_user
)

from ..classes import AppImageErrorImage
from ..thumbnail_click_behaviors import ThumbnailClickBehaviorBackend
from ..literals import (
    DEFAULT_THUMBNAIL_CLICK_BEHAVIOR, IMAGE_CAROUSEL_REQUEST_RATE_FACTOR
)
from ..settings import (
    setting_image_carousel_request_concurrency,
    setting_image_carousel_request_rate,
    setting_image_carousel_retry_attempt_maximum,
    setting_image_carousel_retry_delay_initial,
    setting_image_carousel_retry_delay_maximum
)
from ..utils import get_object_image_data

register = Library()


def get_rest_api_user_rate_per_second():
    """
    Convert the configured REST API authenticated user throttling rate into
    requests per second, so the browser can pace its document image requests
    just under the rate the API will accept. Return None when throttling is
    disabled or no user rate is configured.
    """
    if not setting_throttling_enabled.value:
        return None

    raw_value = setting_throttling_rate_user.value

    if not raw_value:
        return None

    try:
        count, period = raw_value.strip().split('/')
        count = int(count)
        duration = THROTTLING_PERIOD_MULTIPLIER_MAP[period[0]]
    except (IndexError, KeyError, ValueError):
        return None

    if count <= 0 or duration <= 0:
        return None

    return count / duration


@register.simple_tag(name='converter_image_carousel_config')
def tag_converter_image_carousel_config():
    """
    Build the configuration object for the document image carousel browser
    client, serialized as JSON. When the `CONVERTER_IMAGE_CAROUSEL_REQUEST_RATE`
    setting is left at its default, the request rate is derived at render time
    from the live REST API authenticated user throttling rate and set to a
    fraction of it, so the browser stays under the limit the API enforces. Any
    non zero value of the setting overrides that derived default.
    """
    config = {
        'requestConcurrency': setting_image_carousel_request_concurrency.value,
        'retryAttemptMaximum': setting_image_carousel_retry_attempt_maximum.value,
        'retryDelayInitial': setting_image_carousel_retry_delay_initial.value,
        'retryDelayMaximum': setting_image_carousel_retry_delay_maximum.value
    }

    request_rate = setting_image_carousel_request_rate.value

    if not request_rate:
        rest_api_user_rate = get_rest_api_user_rate_per_second()

        if rest_api_user_rate:
            request_rate = rest_api_user_rate * IMAGE_CAROUSEL_REQUEST_RATE_FACTOR

    if request_rate:
        config['requestRate'] = request_rate

    return mark_safe(
        s=json.dumps(obj=config)
    )


@register.simple_tag(name='converter_app_image_error_catch_all')
def tag_converter_app_image_error_catch_all():
    """
    Return the catch all error image, so a page can render its markup into
    a template that the browser reads when a request fails without an error
    image of its own. It is rendered into the page rather than requested so
    that it is available even while the API is failing.
    """
    return AppImageErrorImage.get_catch_all()


@register.simple_tag(
    name='converter_get_object_image_data', takes_context=True
)
def tag_converter_get_object_image_data(
    context, obj, maximum_layer_order=None, transformation_instance_list=None,
    user=None
):
    return get_object_image_data(
        maximum_layer_order=maximum_layer_order, obj=obj,
        transformation_instance_list=transformation_instance_list,
        user=context.get('user', user)
    )


@register.simple_tag(name='converter_thumbnail_click_behavior_render')
def tag_converter_thumbnail_click_behavior_render(
    instance, object_image_data, behavior_name=None, container_class=None,
    disable_title_link=False, display_full_height=False, display_height=None,
    gallery_name=None, image_alt=None, image_template_name=None
):
    """
    Render the clickable thumbnail markup for the given behavior name. The
    behavior is resolved from the `ThumbnailClickBehaviorBackend` registry,
    falling back to the default behavior when the name is empty or unknown so
    the thumbnail always renders.
    """
    behavior_name = behavior_name or DEFAULT_THUMBNAIL_CLICK_BEHAVIOR

    try:
        backend_class = ThumbnailClickBehaviorBackend.get(name=behavior_name)
    except KeyError:
        backend_class = ThumbnailClickBehaviorBackend.get(
            name=DEFAULT_THUMBNAIL_CLICK_BEHAVIOR
        )

    backend = backend_class(
        container_class=container_class,
        disable_title_link=disable_title_link,
        display_full_height=display_full_height, display_height=display_height,
        gallery_name=gallery_name, image_alt=image_alt,
        image_template_name=image_template_name, instance=instance,
        object_image_data=object_image_data
    )

    rendered_html = backend.render()

    return mark_safe(s=rendered_html)
