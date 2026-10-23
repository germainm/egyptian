import logging

import markdown
import nh3
import requests

from django.template import Library
from django.utils.safestring import mark_safe

from mayan.apps.views.http import URL

from ..literals import DEFAULT_HTTP_TIMEOUT, URL_FUNDRAISER_API
from ..markdown_extensions import ExternalLinkExtension

logger = logging.getLogger(name=__name__)

register = Library()


def markdown_render(source):
    md = markdown.Markdown(
        extensions=(
            'attr_list', 'nl2br', ExternalLinkExtension()
        )
    )

    html = md.convert(source=source)

    html_clean = nh3.clean(
        attributes={
            'a': {'href', 'target'},
            'img': {'alt', 'class', 'src', 'style'}
        }, html=html
    )

    html_safe = mark_safe(s=html_clean)

    return html_safe


def get_message_part(name, response_json, url):
    """
    One part of the message, rendered, or nothing when that part alone
    cannot be produced.

    Each part is read and rendered on its own so that it fails on its own. A
    message whose title is missing is still a message worth showing, and a
    fundraiser has already done the work of writing it. Discarding all of it
    over one field would throw that work away, for a reason the reader
    cannot see and the fundraiser cannot correct.
    """
    try:
        source = response_json[name]
    except (KeyError, TypeError):
        logger.debug(
            'The fundraiser message from %s carries no `%s`. Showing the '
            'rest of it.', url, name
        )

        return ''
    else:
        try:
            part_rendered = markdown_render(source=source)
        except (AttributeError, TypeError):
            logger.debug(
                'The `%s` of the fundraiser message from %s is not text. '
                'Showing the rest of it.', name, url
            )

            return ''
        else:
            return part_rendered


@register.simple_tag(name='fundraiser_message_fetch')
def tag_fundraiser_message_fetch(path):
    url = URL(url=URL_FUNDRAISER_API)
    url.path = path

    try:
        response = requests.get(url=url, timeout=DEFAULT_HTTP_TIMEOUT)
    except requests.exceptions.RequestException as exception:
        logger.debug(
            'Unable to retrieve the fundraiser message from %s; %s', url,
            exception
        )

        return ''
    else:
        if not response:
            logger.debug(
                'The fundraiser message request to %s was answered with '
                'status %d.', url, response.status_code
            )

            return ''

        try:
            response_json = response.json()
        except ValueError as exception:
            logger.debug(
                'The fundraiser message from %s is not JSON; %s', url,
                exception
            )

            return ''
        else:
            body_safe = get_message_part(
                name='body', response_json=response_json, url=url
            )
            title_safe = get_message_part(
                name='title', response_json=response_json, url=url
            )

            if not body_safe and not title_safe:
                logger.debug(
                    'The fundraiser message from %s carries neither a body '
                    'nor a title.', url
                )

                return ''

            return {
                'body': body_safe,
                'title': title_safe
            }
