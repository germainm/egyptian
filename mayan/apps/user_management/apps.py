from django.apps import apps
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.classes import ModelPermission
from mayan.apps.acls.permissions import (
    permission_acl_edit, permission_acl_view
)
from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.common.classes import ModelCopy
from mayan.apps.common.menus import (
    menu_list_facet, menu_multi_item, menu_object, menu_related, menu_return,
    menu_secondary, menu_setup, menu_user
)
from mayan.apps.dashboards.dashboards import dashboard_administrator
from mayan.apps.databases.utils import set_field_help_text
from mayan.apps.events.classes import EventModelRegistry, ModelEventType
from mayan.apps.forms import column_widgets
from mayan.apps.logging.classes import ErrorLog
from mayan.apps.navigation.source_columns import SourceColumn
from mayan.apps.rest_api.fields import DynamicSerializerField
from mayan.apps.templating.template_backends import TemplateContextEntry

from .dashboard_widgets import (
    DashboardWidgetGroupTotal, DashboardWidgetUserTotal
)
from .events import (
    event_group_created, event_group_edited, event_user_created,
    event_user_edited
)
from .handlers import handler_initialize_new_user_options
from .links import (
    link_current_user_details, link_group_create, link_group_delete_multiple,
    link_group_delete_single, link_group_edit, link_group_list,
    link_group_setup, link_group_user_list, link_user_create,
    link_user_delete_multiple, link_user_delete_single, link_user_edit,
    link_user_group_list, link_user_list, link_user_set_options,
    link_user_setup, separator_user_label, text_user_label
)
from .methods import (
    get_method_group_init, get_method_group_save, get_method_user_init,
    get_method_user_save, method_group_get_absolute_url,
    method_group_get_users, method_group_users_add, method_group_users_remove,
    method_user_get_absolute_api_url, method_user_get_absolute_url,
    method_user_get_groups, method_user_groups_add, method_user_groups_remove
)
from .permissions import (
    permission_group_delete, permission_group_edit, permission_group_view,
    permission_user_delete, permission_user_edit, permission_user_view
)
from .utils import get_groups, get_users


class UserManagementApp(MayanAppConfig):
    app_namespace = 'user_management'
    app_url = 'accounts'
    has_rest_api = True
    has_tests = True
    name = 'mayan.apps.user_management'
    verbose_name = _(message='User management')

    def ready(self):
        super().ready()

        Group = apps.get_model(app_label='auth', model_name='Group')
        User = get_user_model()
        UserOptions = self.get_model(model_name='UserOptions')

        DynamicSerializerField.add_serializer(
            klass=get_user_model(),
            serializer_class='mayan.apps.user_management.serializers.UserSerializer'
        )

        Group._meta.get_field(field_name='name').verbose_name = _(
            message='Name'
        )
        Group._meta.ordering = ('name',)
        Group._meta.verbose_name = _(message='Group')
        Group._meta.verbose_name_plural = _(message='Groups')

        Group.add_to_class(
            name='__init__', value=get_method_group_init()
        )
        Group.add_to_class(
            name='_ordering_fields', value=('name',)
        )
        Group.add_to_class(
            name='get_absolute_url', value=method_group_get_absolute_url
        )
        Group.add_to_class(
            name='get_users', value=method_group_get_users
        )
        Group.add_to_class(
            name='users_add', value=method_group_users_add
        )
        Group.add_to_class(
            name='users_remove', value=method_group_users_remove
        )
        Group.add_to_class(
            name='save', value=get_method_group_save()
        )

        User._meta.ordering = ('last_name', 'first_name')
        User._meta.verbose_name = _(message='User')
        User._meta.verbose_name_plural = _(message='Users')

        User._meta.get_field(field_name='email').verbose_name = _(
            message='Email'
        )
        User._meta.get_field(
            field_name='first_name'
        ).verbose_name = _(message='First name')
        set_field_help_text(
            field=User._meta.get_field(field_name='first_name'),
            help_text=_(message='The given name of the user.')
        )
        User._meta.get_field(field_name='groups').verbose_name = _(
            message='Groups'
        )
        User._meta.get_field(
            field_name='last_login'
        ).verbose_name = _(message='Last login')
        User._meta.get_field(
            field_name='last_name'
        ).verbose_name = _(message='Last name')
        set_field_help_text(
            field=User._meta.get_field(field_name='last_name'),
            help_text=_(message='The family name of the user.')
        )
        User._meta.get_field(
            field_name='is_active'
        ).verbose_name = _(message='Is active?')
        User._meta.get_field(
            field_name='is_superuser'
        ).verbose_name = _(message='Is super user?')
        User._meta.get_field(
            field_name='password'
        ).verbose_name = _(message='Password')
        User._meta.get_field(
            field_name='username'
        ).verbose_name = _(message='Username')

        User.add_to_class(
            name='__init__', value=get_method_user_init()
        )
        User.add_to_class(
            name='_ordering_fields', value=(
                'email', 'first_name', 'last_name', 'is_active', 'last_login',
                'username'
            )
        )
        User.add_to_class(
            name='get_absolute_api_url',
            value=method_user_get_absolute_api_url
        )
        User.add_to_class(
            name='get_absolute_url', value=method_user_get_absolute_url
        )
        User.add_to_class(
            name='get_groups', value=method_user_get_groups
        )
        User.add_to_class(
            name='groups_add', value=method_user_groups_add
        )
        User.add_to_class(
            name='groups_remove', value=method_user_groups_remove
        )
        User.add_to_class(
            name='save', value=get_method_user_save()
        )

        User.has_usable_password.short_description = _(
            message='Has usable password?'
        )

        EventModelRegistry.register(model=Group)
        EventModelRegistry.register(model=User)

        TemplateContextEntry(
            description=_(message='All the groups'), name='groups',
            value=get_groups
        )
        TemplateContextEntry(
            description=_(message='All the users'), name='users',
            value=get_users
        )

        ModelCopy(
            model=Group, bind_link=True, register_permission=True
        ).add_fields(
            field_names=(
                'name', 'user',
            )
        )
        ModelCopy(model=UserOptions).add_fields(
            field_names=('user', 'block_password_change'),
            field_value_templates={
                'id': '{user.user_options.id}'
            }
        )

        def condition_copy_user_model(instance):
            return not instance.is_superuser and not instance.is_staff

        ModelCopy(
            model=User, condition=condition_copy_user_model, bind_link=True,
            register_permission=True
        ).add_fields(
            field_names=(
                'username', 'first_name', 'last_name', 'email', 'is_active',
                'password', 'groups', 'user_options'
            )
        )

        ModelEventType.register(
            event_types=(event_group_created, event_group_edited),
            model=Group
        )

        ModelEventType.register(
            event_types=(event_user_created, event_user_edited), model=User
        )

        ModelPermission.register(
            model=Group, permissions=(
                permission_acl_edit, permission_acl_view,
                permission_group_delete, permission_group_edit,
                permission_group_view
            )
        )
        ModelPermission.register(
            model=User, permissions=(
                permission_acl_edit, permission_acl_view,
                permission_user_delete, permission_user_edit,
                permission_user_view
            )
        )

        SourceColumn(
            attribute='name', is_identifier=True, is_sortable=True,
            source=Group
        )
        SourceColumn(
            attribute='user_set.count', include_label=True,
            label=_(message='Users'), source=Group
        )

        SourceColumn(
            attribute='username', is_object_absolute_url=True,
            is_identifier=True, is_sortable=True, source=User
        )
        SourceColumn(
            attribute='first_name', include_label=True, is_sortable=True,
            source=User
        )
        SourceColumn(
            attribute='last_name', include_label=True, is_sortable=True,
            source=User
        )
        SourceColumn(
            attribute='email', include_label=True, is_sortable=True,
            source=User
        )
        SourceColumn(
            attribute='last_login', include_label=True, is_sortable=True,
            source=User
        )
        SourceColumn(
            attribute='is_active', include_label=True, is_sortable=True,
            source=User, widget=column_widgets.TwoStateWidget
        )
        SourceColumn(
            attribute='is_superuser', include_label=True, is_sortable=True,
            source=User, widget=column_widgets.TwoStateWidget
        )
        SourceColumn(
            attribute='has_usable_password', include_label=True, source=User,
            widget=column_widgets.TwoStateWidget
        )
        SourceColumn(
            attribute='groups.count', include_label=True,
            label=_(message='Groups'), source=User
        )

        dashboard_administrator.add_widget(
            widget=DashboardWidgetUserTotal, order=99
        )
        dashboard_administrator.add_widget(
            widget=DashboardWidgetGroupTotal, order=99
        )

        error_log = ErrorLog(app_config=self)
        error_log.register_model(model=User)


        menu_list_facet.bind_links(
            links=(
                link_group_user_list,
            ), sources=(Group,)
        )
        menu_multi_item.bind_links(
            links=(link_group_delete_multiple,),
            sources=('user_management:group_list',)
        )
        menu_object.bind_links(
            links=(link_group_edit,),
            sources=(Group,)
        )
        menu_object.bind_links(
            links=(link_group_delete_single,), position=99,
            sources=(Group,)
        )
        menu_related.bind_links(
            links=(link_user_setup,), sources=(
                Group, 'user_management:group_multiple_delete',
                'user_management:group_list', 'user_management:group_create'

            )
        )
        menu_return.bind_links(
            links=(link_group_list,), sources=(
                Group, 'user_management:group_multiple_delete',
                'user_management:group_list', 'user_management:group_create'

            )
        )
        menu_secondary.bind_links(
            links=(link_group_create,), sources=(
                Group, 'user_management:group_multiple_delete',
                'user_management:group_list', 'user_management:group_create'
            )
        )


        menu_list_facet.bind_links(
            links=(
                link_user_group_list, link_user_set_options
            ), sources=(User,)
        )
        menu_multi_item.bind_links(
            links=(link_user_delete_multiple,),
            sources=('user_management:user_list',)
        )
        menu_object.bind_links(
            links=(
                link_user_delete_single, link_user_edit
            ), sources=(User,)
        )
        menu_related.bind_links(
            links=(link_group_setup,), sources=(
                User, 'authentication:user_multiple_set_password',
                'user_management:user_multiple_delete',
                'user_management:user_list', 'user_management:user_create'
            )
        )
        menu_return.bind_links(
            links=(link_user_list,), sources=(
                User, 'authentication:user_multiple_set_password',
                'user_management:user_multiple_delete',
                'user_management:user_list', 'user_management:user_create'
            )
        )
        menu_secondary.bind_links(
            links=(link_user_create,), sources=(
                User, 'authentication:user_multiple_set_password',
                'user_management:user_multiple_delete',
                'user_management:user_list', 'user_management:user_create'
            )
        )
        menu_setup.bind_links(
            links=(link_user_setup, link_group_setup)
        )
        menu_user.bind_links(
            links=(
                text_user_label, separator_user_label,
                link_current_user_details
            ), position=0
        )

        post_save.connect(
            dispatch_uid='user_management_handler_initialize_new_user_options',
            receiver=handler_initialize_new_user_options,
            sender=User
        )
