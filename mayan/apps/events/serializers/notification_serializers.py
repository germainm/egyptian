from django.utils.translation import gettext_lazy as _

from mayan.apps.rest_api import serializers
from mayan.apps.user_management.serializers import UserSerializer

from ..models import Notification

from .event_serializers import EventSerializer


class NotificationSerializer(serializers.HyperlinkedModelSerializer):
    action = EventSerializer(
        label=_(message='Action'), read_only=True
    )
    user = UserSerializer(
        label=_(message='User'), read_only=True
    )

    class Meta:
        extra_kwargs = {
            'url': {
                'label': _(message='URL'),
                'lookup_url_kwarg': 'notification_id',
                'view_name': 'rest_api:notification-detail'
            }
        }
        fields = ('action', 'id', 'read', 'url', 'user')
        model = Notification
        read_only_fields = ('action', 'id', 'url', 'user')
