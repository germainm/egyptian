import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.classes import ModelPermission
from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.common.menus import menu_list_facet, menu_tools
from mayan.apps.events.classes import EventModelRegistry, ModelEventType
from mayan.apps.navigation.source_columns import SourceColumn

from .events import event_user_login_failed, event_user_login_succeeded
from .handlers import handler_user_logged_in, handler_user_login_failed
from .links import (
    link_login_attempt_list, link_user_current_login_attempt_list,
    link_user_login_attempt_list
)
from .permissions import permission_login_attempt_view

logger = logging.getLogger(name=__name__)


class AuthenticationAttemptsApp(MayanAppConfig):
    app_namespace = 'authentication_attempts'
    app_url = 'authentication_attempts'
    has_rest_api = True
    has_tests = True
    name = 'mayan.apps.authentication_attempts'
    verbose_name = _(message='Authentication attempts')

    def ready(self):
        super().ready()

        User = get_user_model()

        LoginAttempt = self.get_model(model_name='LoginAttempt')

        EventModelRegistry.register(
            bind_events_link=False, bind_subscription_link=False,
            delete_events_on_object_deletion=True, model=LoginAttempt,
            register_permissions=False
        )

        ModelEventType.register(
            model=User, event_types=(
                event_user_login_failed, event_user_login_succeeded
            )
        )

        ModelPermission.register(
            model=User, permissions=(
                permission_login_attempt_view,
            )
        )
        ModelPermission.register_inheritance(
            model=LoginAttempt, related='user'
        )

        SourceColumn(
            attribute='datetime', is_identifier=True, is_sortable=True,
            source=LoginAttempt
        )
        SourceColumn(
            attribute='username', is_sortable=True, source=LoginAttempt
        )
        SourceColumn(
            attribute='user', empty_value=_(message='Unknown'),
            source=LoginAttempt
        )
        SourceColumn(
            attribute='get_result_display', include_label=True,
            is_sortable=True, label=_(message='Result'), sort_field='result',
            source=LoginAttempt
        )
        SourceColumn(
            attribute='get_source_display', include_label=True,
            is_sortable=True, sort_field='source', source=LoginAttempt,
            label=_(message='Source')
        )
        SourceColumn(
            attribute='ip_address', empty_value=_(message='None'),
            include_label=True, source=LoginAttempt
        )
        SourceColumn(
            attribute='user_agent', empty_value=_(message='None'),
            include_label=True, source=LoginAttempt
        )

        menu_tools.bind_links(
            links=(link_login_attempt_list,)
        )

        menu_list_facet.bind_links(
            links=(link_user_login_attempt_list,), sources=(User,)
        )

        menu_list_facet.bind_links(
            links=(link_user_current_login_attempt_list,),
            sources=(User,)
        )

        user_logged_in.connect(
            dispatch_uid='authentication_attempts_handler_user_logged_in',
            receiver=handler_user_logged_in, sender=User
        )
        user_login_failed.connect(
            dispatch_uid='authentication_attempts_handler_user_login_failed',
            receiver=handler_user_login_failed
        )
