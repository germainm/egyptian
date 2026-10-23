from django.utils.translation import gettext_lazy as _

from mayan.apps.rest_api import serializers
from mayan.apps.user_management.serializers import UserSerializer

from .models import LoginAttempt


class LoginAttemptSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        label=_(message='URL'), lookup_url_kwarg='login_attempt_id',
        view_name='rest_api:login_attempt-detail'
    )
    user = UserSerializer(read_only=True)

    class Meta:
        fields = (
            'datetime', 'id', 'ip_address', 'result', 'source', 'url',
            'user', 'user_agent', 'username'
        )
        model = LoginAttempt
        read_only_fields = fields
