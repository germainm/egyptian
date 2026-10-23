from django.conf import settings

from mayan.apps.views.http import URL

from .settings import (
    setting_organization_installation_url, setting_organization_url_base_path
)


def do_asset_urls_apply_base_path():
    base_path = setting_organization_url_base_path.value

    if not base_path:
        return

    for setting_name in ('MEDIA_URL', 'STATIC_URL'):
        value = getattr(settings, setting_name, None)
        new_value = get_url_with_base_path(base_path=base_path, url=value)

        if new_value != value:
            setattr(settings, setting_name, new_value)


def get_url_with_base_path(base_path, url):
    if not url:
        return url

    if '://' in url or url.startswith('//'):
        return url

    prefix = '/{}'.format(base_path)

    if url.startswith('/'):
        normalized_url = url
    else:
        normalized_url = '/{}'.format(url)

    if normalized_url == prefix or normalized_url.startswith(
        '{}/'.format(prefix)
    ):
        return url

    return '{}{}'.format(prefix, normalized_url)


def get_organization_installation_url(request=None):
    installation_url = setting_organization_installation_url.value
    installation_path = setting_organization_url_base_path.value

    if installation_url:
        return URL(
            path=installation_path, url=installation_url
        ).to_string()
    elif request:
        return URL(
            netloc=request.get_host(), path=installation_path,
            port=request.get_port(), scheme=request.scheme
        ).to_string()
    else:
        return ''
