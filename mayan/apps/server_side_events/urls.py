from django.urls import re_path

from .api_views import APIEventStreamView

api_urls = [
    re_path(
        route=r'^server_side_events/stream/$', name='event_stream',
        view=APIEventStreamView.as_view()
    )
]
