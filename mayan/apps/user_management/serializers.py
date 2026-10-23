from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import ValidationError

from mayan.apps.rest_api import serializers
from mayan.apps.rest_api.relations import FilteredPrimaryKeyRelatedField

from .permissions import permission_user_edit
from .querysets import get_user_queryset


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    users_url = serializers.HyperlinkedIdentityField(
        help_text=_(
            message='URL of the API endpoint showing the list users of this '
            'group.'
        ), label=_(message='Users URL'), lookup_url_kwarg='group_id',
        view_name='rest_api:group-user-list'
    )
    users_add_url = serializers.HyperlinkedIdentityField(
        label=_(message='Users add URL'), lookup_url_kwarg='group_id',
        view_name='rest_api:group-user-add'
    )
    users_remove_url = serializers.HyperlinkedIdentityField(
        label=_(message='Users remove URL'), lookup_url_kwarg='group_id',
        view_name='rest_api:group-user-remove'
    )

    class Meta:
        extra_kwargs = {
            'url': {
                'label': _(message='URL'),
                'lookup_url_kwarg': 'group_id',
                'view_name': 'rest_api:group-detail'
            }
        }
        fields = (
            'id', 'name', 'url', 'users_url', 'users_add_url',
            'users_remove_url'
        )
        model = Group


class GroupUserAddSerializer(serializers.Serializer):
    user = FilteredPrimaryKeyRelatedField(
        help_text=_(
            message='Primary key of the user to add to the group.'
        ), label=_(message='User ID'), source_permission=permission_user_edit,
        source_queryset_method='get_user_source_queryset'
    )

    def get_user_source_queryset(self):
        return get_user_queryset(
            user=self.context['request'].user
        )


class GroupUserRemoveSerializer(serializers.Serializer):
    user = FilteredPrimaryKeyRelatedField(
        help_text=_(
            message='Primary key of the user to remove from the group.'
        ), label=_(message='User ID'), source_permission=permission_user_edit,
        source_queryset_method='get_user_source_queryset'
    )

    def get_user_source_queryset(self):
        return get_user_queryset(
            user=self.context['request'].user
        )


class UserSerializer(serializers.HyperlinkedModelSerializer):
    groups_url = serializers.HyperlinkedIdentityField(
        help_text=_(
            message='URL of the API endpoint showing the list groups this '
            'user belongs to.'
        ), label=_(message='Groups URL'), lookup_url_kwarg='user_id',
        view_name='rest_api:user-group-list'
    )
    password = serializers.CharField(
        label=_(message='Password'), required=False, style={
            'input_type': 'password'
        }, write_only=True
    )

    class Meta:
        extra_kwargs = {
            'url': {
                'label': _(message='URL'),
                'lookup_url_kwarg': 'user_id',
                'view_name': 'rest_api:user-detail'
            }
        }
        fields = (
            'first_name', 'date_joined', 'email', 'groups_url',
            'id', 'is_active', 'last_login', 'last_name', 'password', 'url',
            'username'
        )
        model = get_user_model()
        read_only_fields = ('is_active', 'last_login', 'date_joined')
        write_only_fields = ('password',)

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = super().create(validated_data)

        if password:
            instance._event_ignore = True
            instance.set_password(raw_password=password)
            instance.save()

        return instance

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.set_password(
                raw_password=validated_data['password']
            )
            validated_data.pop('password')

        return super().update(
            instance=instance, validated_data=validated_data
        )

    def validate(self, data):
        if 'password' in data:
            validate_password(
                password=data['password'], user=self.instance
            )

        return data


class UserDetailSerializer(UserSerializer):
    def validate_password(self, value):
        if self.instance and (
            self.instance.is_staff or self.instance.is_superuser
        ):
            raise ValidationError(
                _(
                    message='Changing the password of staff or super user '
                    'accounts through this endpoint is not allowed. Use '
                    'administration tools to perform this operation.'
                )
            )

        return value
