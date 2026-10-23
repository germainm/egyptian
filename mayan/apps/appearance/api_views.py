from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from mayan.apps.acls.models import AccessControlList
from mayan.apps.user_management.permissions import permission_user_edit
from mayan.apps.user_management.querysets import get_user_queryset

from .classes import Theme
from .literals import USER_THEME_SETTING_KEY, USER_THEME_SETTING_NAMESPACE
from .models import UserSetting
from .serializers import ThemeSettingSerializer
from .settings import setting_theme_user_selection_enabled


class APIThemeView(GenericAPIView):
    """
    get: Return the theme of the current user.
    put: Set the theme of the current user.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = ThemeSettingSerializer

    def get(self, request, *args, **kwargs):
        theme = Theme.get_for_request(request=request)

        serializer = self.get_serializer(
            instance={
                'theme': getattr(theme, 'name', None)
            }
        )
        return Response(data=serializer.data)

    def put(self, request, *args, **kwargs):
        if not setting_theme_user_selection_enabled.value:
            raise PermissionDenied(
                detail=_(message='Theme selection is disabled.')
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        UserSetting.objects.do_value_set(
            _event_actor=request.user,
            key=USER_THEME_SETTING_KEY,
            namespace=USER_THEME_SETTING_NAMESPACE, user=request.user,
            value=serializer.validated_data['theme']
        )

        return Response(data=serializer.data)


class APIUserThemeView(GenericAPIView):
    """
    get: Return the theme of the selected user.
    put: Set the theme of the selected user.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = ThemeSettingSerializer

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
            key=USER_THEME_SETTING_KEY,
            namespace=USER_THEME_SETTING_NAMESPACE, user=user
        )
        theme = Theme.get(name=name) or Theme.get_default()

        serializer = self.get_serializer(
            instance={
                'theme': getattr(theme, 'name', None)
            }
        )
        return Response(data=serializer.data)

    def put(self, request, *args, **kwargs):
        user = self.get_user()

        if not setting_theme_user_selection_enabled.value:
            raise PermissionDenied(
                detail=_(message='Theme selection is disabled.')
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        UserSetting.objects.do_value_set(
            _event_actor=request.user, key=USER_THEME_SETTING_KEY,
            namespace=USER_THEME_SETTING_NAMESPACE, user=user,
            value=serializer.validated_data['theme']
        )

        return Response(data=serializer.data)
