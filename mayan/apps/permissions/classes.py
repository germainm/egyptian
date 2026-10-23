import itertools
import logging

from django.apps import apps
from django.core.exceptions import PermissionDenied
from django.db.utils import OperationalError, ProgrammingError
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.class_mixins import AppsModuleLoaderMixin
from mayan.apps.common.collections import ClassCollection

logger = logging.getLogger(name=__name__)


class PermissionNamespace:
    _registry = {}

    @classmethod
    def all(cls):
        return cls._registry.values()

    @classmethod
    def get(cls, name):
        return cls._registry[name]

    def __init__(self, name, label):
        self.name = name
        self.label = label
        self.permissions = []
        self.__class__._registry[name] = self

    def __str__(self):
        return str(self.label)

    def add_permission(self, name, label):
        permission = Permission(namespace=self, name=name, label=label)
        self.permissions.append(permission)
        return permission


class Permission(AppsModuleLoaderMixin):
    _imported_app = []
    _loader_module_name = 'permissions'
    _registry = {}

    @classmethod
    def all(cls):
        return PermissionCollection(
            sorted(
                cls._registry.values(), key=lambda x: x.namespace.name
            )
        )

    @classmethod
    def check_user_permission(cls, permission, user):
        if permission.stored_permission.user_has_this(user=user):
            return True

        logger.debug(
            'User "%s" does not have permission "%s"', user, permission
        )
        raise PermissionDenied(
            _(message='Insufficient permission.')
        )

    @classmethod
    def get(cls, pk):
        return cls._registry[pk]

    @classmethod
    def get_choices(cls):
        results = PermissionCollection()

        groups_permissions = itertools.groupby(
            cls.all(), lambda entry: entry.namespace
        )

        for namespace, permissions in groups_permissions:
            permission_options = [
                (permission.pk, permission) for permission in permissions
            ]
            results.append(
                (namespace, permission_options)
            )

        return results

    @classmethod
    def post_load_modules(cls):
        StoredPermission = apps.get_model(
            app_label='permissions', model_name='StoredPermission'
        )

        try:
            """
            Check is the table is ready.
            If not, this will log an error similar to this:
            2023-12-12 09:00:54.666 UTC [79] ERROR:  relation "permissions_storedpermission" does not exist at character 22
            2023-12-12 09:00:54.666 UTC [79] STATEMENT:  SELECT 1 AS "a" FROM "permissions_storedpermission" LIMIT 1
            This error is expected and should be ignored.
            """
            StoredPermission.objects.exists()
        except (OperationalError, ProgrammingError):
            """
            This error is expected when trying to initialize the
            stored permissions during the initial creation of the
            database. Can be safely ignored under that situation.
            """
        else:
            for permission in cls.all():
                permission.stored_permission

    @classmethod
    def invalidate_cache(cls):
        for permission in cls.all():
            try:
                del permission.stored_permission
            except AttributeError:
                """Stored permission was not cached."""

    def __init__(self, namespace, name, label):
        self.namespace = namespace
        self.name = name
        self.label = label
        self.pk = self.get_pk()
        self.__class__._registry[self.pk] = self

    def __repr__(self):
        return self.pk

    def __str__(self):
        return str(self.label)

    def get_pk(self):
        return '{}.{}'.format(self.namespace.name, self.name)

    @cached_property
    def stored_permission(self):
        StoredPermission = apps.get_model(
            app_label='permissions', model_name='StoredPermission'
        )

        stored_permission, created = StoredPermission.objects.get_or_create(
            name=self.name, namespace=self.namespace.name
        )
        return stored_permission


class PermissionCollection(ClassCollection):
    klass = Permission
