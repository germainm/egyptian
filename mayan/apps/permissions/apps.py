from django.apps import apps
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.classes import ModelPermission
from mayan.apps.acls.permissions import (
    permission_acl_edit, permission_acl_view
)
from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.app_manager.classes import InitializationStep
from mayan.apps.app_manager.literals import PROCESS_UPGRADE
from mayan.apps.app_manager.runlevels import runlevel_maintenance
from mayan.apps.common.classes import ModelCopy
from mayan.apps.common.menus import (
    menu_list_facet, menu_multi_item, menu_object, menu_related, menu_return,
    menu_secondary, menu_setup
)
from mayan.apps.dashboards.dashboards import dashboard_administrator
from mayan.apps.events.classes import EventModelRegistry, ModelEventType
from mayan.apps.navigation.source_columns import SourceColumn
from mayan.apps.rest_api.fields import DynamicSerializerField
from mayan.apps.user_management.links import link_group_list

from .classes import Permission
from .dashboard_widgets import DashboardWidgetRoleTotal
from .events import event_role_created, event_role_edited
from .handlers import handler_permission_initialize
from .initializers import initializer_purge_permissions
from .links import (
    link_group_role_list, link_role_create, link_role_delete_single,
    link_role_delete_multiple, link_role_edit, link_role_group_list,
    link_role_list, link_role_permission_list, link_role_setup
)
from .methods import method_group_roles_add, method_group_roles_remove
from .permissions import (
    permission_role_delete, permission_role_edit, permission_role_view
)


class PermissionsApp(MayanAppConfig):
    app_namespace = 'permissions'
    app_url = 'permissions'
    has_rest_api = True
    has_tests = True
    name = 'mayan.apps.permissions'
    verbose_name = _(message='Permissions')

    def ready(self):
        super().ready()

        Role = self.get_model(model_name='Role')
        StoredPermission = self.get_model(model_name='StoredPermission')
        Group = apps.get_model(app_label='auth', model_name='Group')

        DynamicSerializerField.add_serializer(
            klass=Role,
            serializer_class='mayan.apps.permissions.serializers.RoleSerializer'
        )

        Group.add_to_class(name='roles_add', value=method_group_roles_add)
        Group.add_to_class(
            name='roles_remove', value=method_group_roles_remove
        )

        EventModelRegistry.register(model=Role)
        EventModelRegistry.register(
            model=StoredPermission, bind_subscription_link=False
        )

        InitializationStep(
            function=initializer_purge_permissions,
            label=_(message='Purge obsolete permissions'),
            name='permissions.purge_permissions', process=PROCESS_UPGRADE,
            runlevel=runlevel_maintenance
        )

        ModelCopy(
            bind_link=True, model=Role, register_permission=True
        ).add_fields(
            field_names=(
                'label', 'permissions', 'groups',
            ),
        )
        ModelCopy.add_fields_lazy(
            model=Group, field_names=(
                'roles',
            ),
        )

        ModelEventType.register(
            event_types=(event_role_created, event_role_edited), model=Role
        )

        ModelPermission.register(
            model=Role, permissions=(
                permission_acl_edit, permission_acl_view,
                permission_role_delete, permission_role_edit,
                permission_role_view
            )
        )

        Permission.load_modules()

        SourceColumn(
            attribute='label', is_identifier=True, is_sortable=True,
            source=Role
        )
        SourceColumn(
            attribute='get_permission_count', include_label=True,
            source=Role
        )
        SourceColumn(
            attribute='get_group_count', kwargs={'user': 'request.user'},
            include_label=True, label=_(message='Group count'), source=Role
        )

        dashboard_administrator.add_widget(
            widget=DashboardWidgetRoleTotal, order=99
        )


        menu_list_facet.bind_links(
            links=(link_group_role_list,), sources=(Group,)
        )

        menu_related.bind_links(
            links=(link_role_list,), sources=(
                'user_management:group_multiple_delete',
                'user_management:group_list', 'user_management:group_create',
                Group
            )
        )


        menu_list_facet.bind_links(
            links=(
                link_role_group_list, link_role_permission_list
            ), sources=(Role,)
        )
        menu_multi_item.bind_links(
            links=(link_role_delete_multiple,),
            sources=('permissions:role_list',)
        )
        menu_object.bind_links(
            links=(
                link_role_delete_single, link_role_edit
            ), sources=(Role,)
        )
        menu_related.bind_links(
            links=(link_group_list,), sources=(
                'permissions:role_create',
                'permissions:role_multiple_delete',
                'permissions:role_list', Role
            )
        )
        menu_return.bind_links(
            links=(link_role_list,), sources=(
                Role, 'permissions:role_create',
                'permissions:role_multiple_delete',
                'permissions:role_list'
            )
        )
        menu_secondary.bind_links(
            links=(link_role_create,), sources=(
                Role, 'permissions:role_create',
                'permissions:role_multiple_delete',
                'permissions:role_list'
            )
        )
        menu_setup.bind_links(
            links=(link_role_setup,)
        )

        post_migrate.connect(
            dispatch_uid='permissions_handler_permission_initialize',
            receiver=handler_permission_initialize,
            sender=self
        )
