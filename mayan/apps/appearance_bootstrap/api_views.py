from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from mayan.apps.acls.models import AccessControlList
from mayan.apps.appearance.models import UserSetting
from mayan.apps.user_management.permissions import permission_user_edit
from mayan.apps.user_management.querysets import get_user_queryset

from .classes import ColorMode
from .literals import (
    USER_COLOR_MODE_SETTING_KEY, USER_COLOR_MODE_SETTING_NAMESPACE
)
from .serializers import ColorModeSettingSerializer
from .settings import setting_color_mode_user_selection_enabled


class APIColorModeView(GenericAPIView):
    """
    get: Return the color mode of the current user.
    put: Set the color mode of the current user.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = ColorModeSettingSerializer

    def get(self, request, *args, **kwargs):
        color_mode = ColorMode.get_for_request(request=request)

        serializer = self.get_serializer(
            instance={
                'color_mode': getattr(color_mode, 'name', None)
            }
        )
        return Response(data=serializer.data)

    def put(self, request, *args, **kwargs):
        if not setting_color_mode_user_selection_enabled.value:
            raise PermissionDenied(
                detail=_(message='Color mode selection is disabled.')
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        UserSetting.objects.do_value_set(
            _event_actor=request.user,
            key=USER_COLOR_MODE_SETTING_KEY,
            namespace=USER_COLOR_MODE_SETTING_NAMESPACE, user=request.user,
            value=serializer.validated_data['color_mode']
        )

        return Response(data=serializer.data)


class APIUserColorModeView(GenericAPIView):
    """
    get: Return the color mode of the selected user.
    put: Set the color mode of the selected user.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = ColorModeSettingSerializer

    def get_user(self):
        queryset = AccessControlList.objects.restrict_queryset(
            permission=permission_user_edit,
            queryset=get_user_queryset(user=self.request.user),
            user=self.request.user
        )
        return get_object_or_404(
            queryset, pk=self.kwargs['user_id']
        )

    def get(self, request, *args, **kwargs):
        user = self.get_user()

        name = UserSetting.objects.do_value_get(
            key=USER_COLOR_MODE_SETTING_KEY,
            namespace=USER_COLOR_MODE_SETTING_NAMESPACE, user=user
        )
        color_mode = ColorMode.get(name=name) or ColorMode.get_default()

        serializer = self.get_serializer(
            instance={
                'color_mode': getattr(color_mode, 'name', None)
            }
        )
        return Response(data=serializer.data)

    def put(self, request, *args, **kwargs):
        user = self.get_user()

        if not setting_color_mode_user_selection_enabled.value:
            raise PermissionDenied(
                detail=_(message='Color mode selection is disabled.')
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        UserSetting.objects.do_value_set(
            _event_actor=request.user, key=USER_COLOR_MODE_SETTING_KEY,
            namespace=USER_COLOR_MODE_SETTING_NAMESPACE, user=user,
            value=serializer.validated_data['color_mode']
        )

        return Response(data=serializer.data)
