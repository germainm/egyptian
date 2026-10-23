from django.core.exceptions import PermissionDenied

from rest_framework.permissions import BasePermission

from mayan.apps.acls.models import AccessControlList
from mayan.apps.permissions.classes import Permission


class MayanPermission(BasePermission):
    def get_mayan_object_permission(self, request, view):
        try:
            method_get_mayan_object_permission_map = getattr(
                view, 'get_mayan_object_permission_map'
            )
        except AttributeError:
            mayan_object_permission_map = getattr(
                view, 'mayan_object_permission_map', {}
            )

            permission = mayan_object_permission_map.get(
                request.method, None
            )
            return permission
        else:
            return method_get_mayan_object_permission_map()

    def get_mayan_view_permission(self, request, view):
        try:
            method_get_mayan_view_permission_map = getattr(
                view, 'get_mayan_view_permission_map'
            )
        except AttributeError:
            mayan_view_permission_map = getattr(
                view, 'mayan_view_permission_map', {}
            )

            permission = mayan_view_permission_map.get(
                request.method, None
            )

            return permission
        else:
            return method_get_mayan_view_permission_map()

    def has_object_permission(self, request, view, obj):
        permission = self.get_mayan_object_permission(
            request=request, view=view
        )
        user = request.user

        if permission:
            if user.is_authenticated:
                try:
                    AccessControlList.objects.check_access(
                        obj=obj, permission=permission, user=user
                    )
                except PermissionDenied:
                    return False
                else:
                    return True
            else:
                return False
        else:
            return True

    def has_permission(self, request, view):
        permission = self.get_mayan_view_permission(
            request=request, view=view
        )
        user = request.user

        if permission:
            if user.is_authenticated:
                try:
                    Permission.check_user_permission(
                        permission=permission, user=user
                    )
                except PermissionDenied:
                    return False
                else:
                    return True
            else:
                return False
        else:
            return True
