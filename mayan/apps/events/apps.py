from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.classes import ModelPermission
from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.common.menus import (
    menu_list_facet, menu_multi_item, menu_object, menu_return,
    menu_secondary, menu_tools, menu_topbar
)
from mayan.apps.forms import column_widgets
from mayan.apps.navigation.source_columns import SourceColumn

from .classes import EventTypeNamespace
from .handlers import handler_stored_event_type_pk_cache_clear
from .html_widgets import widget_event_actor_link, widget_event_type_link
from .links import (
    link_event_list, link_event_list_clear, link_event_list_export,
    link_event_type_subscription_list, link_notification_delete_multiple,
    link_notification_delete_single, link_notification_list,
    link_notification_mark_read, link_notification_mark_read_all,
    link_object_event_list_clear, link_object_event_list_export,
    link_user_object_subscription_list
)


class EventsApp(MayanAppConfig):
    app_namespace = 'events'
    app_url = 'events'
    has_rest_api = True
    has_tests = True
    name = 'mayan.apps.events'
    verbose_name = _(message='Events')

    def ready(self):
        super().ready()

        Action = apps.get_model(app_label='actstream', model_name='Action')
        Notification = self.get_model(model_name='Notification')
        ObjectEventSubscription = self.get_model(
            model_name='ObjectEventSubscription'
        )
        StoredEventType = self.get_model(model_name='StoredEventType')

        User = get_user_model()

        EventTypeNamespace.load_modules()

        Action.add_to_class(
            name='_ordering_fields', value=('timestamp',)
        )

        ModelPermission.register_inheritance(
            fk_field_cast=models.CharField, model=Action,
            related='action_object'
        )
        ModelPermission.register_inheritance(
            fk_field_cast=models.CharField, model=Action, related='actor'
        )
        ModelPermission.register_inheritance(
            fk_field_cast=models.CharField, model=Action, related='target'
        )

        ModelPermission.register_inheritance(
            fk_field_cast=models.CharField, model=Notification,
            related='action__action_object'
        )
        ModelPermission.register_inheritance(
            fk_field_cast=models.CharField, model=Notification,
            related='action__actor'
        )
        ModelPermission.register_inheritance(
            fk_field_cast=models.CharField, model=Notification,
            related='action__target'
        )

        ModelPermission.register_inheritance(
            model=ObjectEventSubscription, related='content_object'
        )

        SourceColumn(
            attribute='timestamp', is_identifier=True,
            is_sortable=True, label=_(message='Date and time'), name='timestamp',
            source=Action
        )
        SourceColumn(
            func=widget_event_actor_link, label=_(message='Actor'),
            include_label=True, source=Action
        )
        SourceColumn(
            func=widget_event_type_link, label=_(message='Event'),
            include_label=True, name='event_type', source=Action
        )
        SourceColumn(
            attribute='target', label=_(message='Target'), include_label=True,
            name='target', source=Action, widget=column_widgets.ObjectLinkWidget
        )
        SourceColumn(
            attribute='action_object', label=_(message='Action object'),
            include_label=True, source=Action, widget=column_widgets.ObjectLinkWidget
        )


        SourceColumn(
            attribute='namespace', label=_(message='Namespace'),
            source=StoredEventType

        )
        SourceColumn(
            attribute='label', label=_(message='Label'), source=StoredEventType
        )


        SourceColumn(
            attribute='action__timestamp', is_identifier=True,
            is_sortable=True, label=_(message='Date and time'), source=Notification
        )
        SourceColumn(
            func=widget_event_actor_link, include_label=True,
            label=_(message='Actor'), kwargs={'attribute': '"action"'},
            source=Notification
        )
        SourceColumn(
            func=widget_event_type_link, include_label=True,
            label=_(message='Event'), kwargs={'attribute': '"action"'},
            source=Notification
        )
        SourceColumn(
            attribute='action.target', include_label=True,
            label=_(message='Target'), source=Notification,
            widget=column_widgets.ObjectLinkWidget
        )
        SourceColumn(
            attribute='action.action_object', include_label=True,
            label=_(message='Action object'), source=Notification,
            widget=column_widgets.ObjectLinkWidget
        )
        SourceColumn(
            attribute='read', include_label=True, is_sortable=True,
            label=_(message='Seen'), source=Notification,
            widget=column_widgets.TwoStateWidget
        )


        SourceColumn(
            attribute='content_object', include_label=True,
            label=_(message='Object'), source=ObjectEventSubscription,
            widget=column_widgets.ObjectLinkWidget
        )
        SourceColumn(
            attribute='stored_event_type', include_label=True,
            label=_(message='Event type'), source=ObjectEventSubscription
        )


        menu_secondary.bind_links(
            links=(link_event_list_clear,),
            sources=(
                'events:event_list', 'events:event_list_clear'
            )
        )
        menu_secondary.bind_links(
            links=(link_object_event_list_clear,),
            sources=(
                'events:object_event_list', 'events:object_event_list_clear',
                'events:object_event_list_export'
            )
        )


        menu_secondary.bind_links(
            links=(link_event_list_export,),
            sources=(
                'events:event_list', 'events:event_list_export'
            )
        )
        menu_secondary.bind_links(
            links=(link_object_event_list_export,),
            sources=(
                'events:object_event_list', 'events:object_event_list_clear',
                'events:object_event_list_export'
            )
        )


        menu_object.bind_links(
            links=(
                link_notification_delete_single, link_notification_mark_read,
            ), sources=(Notification,)
        )
        menu_multi_item.bind_links(
            links=(
                link_notification_delete_multiple,
            ), sources=('events:user_notifications_list',)
        )
        menu_secondary.bind_links(
            links=(link_notification_mark_read_all,),
            sources=(
                'events:notification_mark_read',
                'events:notification_mark_read_all',
                'events:user_notifications_list'
            )
        )


        menu_list_facet.bind_links(
            links=(
                link_event_type_subscription_list,
                link_user_object_subscription_list,
            ), sources=(User,)
        )


        menu_return.bind_links(
            links=(link_event_list,), sources=(
                'events:event_list', 'events:event_list_clear',
                'events:event_list_export'
            )
        )
        menu_topbar.bind_links(
            links=(link_notification_list,), position=30
        )
        menu_tools.bind_links(
            links=(link_event_list,)
        )

        post_delete.connect(
            dispatch_uid='events_handler_stored_event_type_pk_cache_clear_delete',
            receiver=handler_stored_event_type_pk_cache_clear,
            sender=StoredEventType
        )
        post_save.connect(
            dispatch_uid='events_handler_stored_event_type_pk_cache_clear_save',
            receiver=handler_stored_event_type_pk_cache_clear,
            sender=StoredEventType
        )
