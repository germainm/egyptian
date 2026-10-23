import csv
from functools import partial
import logging

from furl import furl

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db.utils import OperationalError, ProgrammingError
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from actstream import action

from mayan.apps.common.class_mixins import AppsModuleLoaderMixin
from mayan.apps.common.menus import menu_list_facet
from mayan.apps.databases.literals import DEFAULT_QUERYSET_ITERATOR_CHUNK_SIZE
from mayan.apps.organizations.utils import get_organization_installation_url

from .exceptions import EventError
from .links import (
    link_object_event_list, link_object_event_type_user_subscription_list
)
from .literals import (
    DEFAULT_EVENT_LIST_EXPORT_FILENAME, EVENT_EVENTS_CLEARED_NAME,
    EVENT_EVENTS_EXPORTED_NAME, EVENT_TYPE_NAMESPACE_NAME,
    TEXT_UNKNOWN_EVENT_ID
)
from .permissions import (
    permission_events_clear, permission_events_export, permission_events_view
)
from .settings import setting_disable_asynchronous_mode

DEFAULT_ACTION_EXPORTER_FIELD_NAMES = (
    'timestamp', 'id', 'actor_content_type', 'actor_object_id', 'actor',
    'target_content_type', 'target_object_id', 'target', 'verb',
    'action_object_content_type', 'action_object_object_id', 'action_object'
)
logger = logging.getLogger(name=__name__)


class ActionExporter:
    def __init__(self, queryset, field_names=None):
        self.field_names = field_names or DEFAULT_ACTION_EXPORTER_FIELD_NAMES
        self.queryset = queryset

    def export(self, file_object, user=None):
        AccessControlList = apps.get_model(
            app_label='acls', model_name='AccessControlList'
        )
        if user:
            self.queryset = AccessControlList.objects.restrict_queryset(
                queryset=self.queryset,
                permission=permission_events_export,
                user=user
            )

        writer = csv.writer(
            file_object, delimiter=',', quotechar='"',
            quoting=csv.QUOTE_MINIMAL
        )
        file_object.write(
            ','.join(
                self.field_names + ('\n',)
            )
        )

        for entry in self.queryset.iterator(chunk_size=DEFAULT_QUERYSET_ITERATOR_CHUNK_SIZE):
            row = [
                str(
                    getattr(entry, field_name)
                ) for field_name in self.field_names
            ]
            writer.writerow(row)

    def export_to_download_file(
        self, organization_installation_url=None, user=None
    ):
        event_type_namespace = EventTypeNamespace.get(
            name=EVENT_TYPE_NAMESPACE_NAME
        )
        event_events_exported = event_type_namespace.get_event(
            name=EVENT_EVENTS_EXPORTED_NAME
        )

        DownloadFile = apps.get_model(
            app_label='storage', model_name='DownloadFile'
        )
        Message = apps.get_model(
            app_label='messaging', model_name='Message'
        )

        content_function = partial(self.export, user=user)

        download_file = DownloadFile.objects.create_from_content_function(
            binary=False, content_function=content_function,
            filename=DEFAULT_EVENT_LIST_EXPORT_FILENAME,
            label=_(message='Event list export to CSV'), user=user
        )

        event_events_exported.commit(
            actor=user, target=download_file
        )

        if user:
            if not organization_installation_url:
                organization_installation_url = get_organization_installation_url()

            download_list_url = furl(organization_installation_url).join(
                reverse(viewname='storage:download_file_list')
            ).tostr()
            download_url = furl(organization_installation_url).join(
                reverse(
                    kwargs={'download_file_id': download_file.pk},
                    viewname='storage:download_file_download'
                )
            ).tostr()

            Message.objects.create(
                sender_object=download_file,
                user=user,
                subject=_(message='Events exported.'),
                body=_(
                    message='The event list has been exported and is '
                    'available for download using the link: %(download_url)s '
                    'or from the downloads area (%(download_list_url)s).'
                ) % {
                    'download_list_url': download_list_url,
                    'download_url': download_url
                }
            )


class EventModelRegistry:
    _registry = set()

    @classmethod
    def register(
        cls, model, acl_bind_link=True, bind_events_link=True,
        bind_subscription_link=True, delete_events_on_object_deletion=False,
        exclude=None, menu=None, register_permissions=True
    ):
        from django.db.models.signals import post_delete

        from actstream import registry

        from mayan.apps.acls.classes import ModelPermission

        from .handlers import handler_delete_object_events

        AccessControlList = apps.get_model(
            app_label='acls', model_name='AccessControlList'
        )
        StoredPermission = apps.get_model(
            app_label='permissions', model_name='StoredPermission'
        )

        event_type_namespace = EventTypeNamespace.get(
            name=EVENT_TYPE_NAMESPACE_NAME
        )
        event_events_cleared = event_type_namespace.get_event(
            name=EVENT_EVENTS_CLEARED_NAME
        )
        event_events_exported = event_type_namespace.get_event(
            name=EVENT_EVENTS_EXPORTED_NAME
        )

        if model not in cls._registry:
            cls._registry.add(model)
            registry.register(model)

            if delete_events_on_object_deletion:
                post_delete.connect(
                    dispatch_uid='events_handler_delete_object_events_{}'.format(
                        model._meta.label
                    ),
                    receiver=handler_delete_object_events, sender=model
                )

            menu = menu or menu_list_facet

            if bind_events_link:
                menu.bind_links(
                    exclude=exclude,
                    links=(
                        link_object_event_list,
                    ), sources=(model,)
                )

            if bind_subscription_link:
                menu.bind_links(
                    exclude=exclude,
                    links=(
                        link_object_event_type_user_subscription_list,
                    ), sources=(model,)
                )

            if register_permissions and not issubclass(model, (AccessControlList, StoredPermission)):
                ModelPermission.register(
                    exclude=exclude,
                    model=model, permissions=(
                        permission_events_clear, permission_events_export,
                        permission_events_view
                    ), bind_link=acl_bind_link
                )

                ModelEventType.register(
                    event_types=(
                        event_events_cleared, event_events_exported
                    ), model=model
                )


class EventTypeNamespaceMetaclass(type):
    _registry = {}

    @classmethod
    def all(cls):
        return sorted(
            cls._registry.values()
        )

    @classmethod
    def get(cls, name):
        return cls._registry[name]

    def __call__(cls, name, label, **kwargs):
        if name in cls._registry:
            return cls._registry[name]
        else:
            instance = super().__call__(name=name, label=label, **kwargs)
            cls._registry[name] = instance
            return instance


class EventTypeNamespace(
    AppsModuleLoaderMixin, metaclass=EventTypeNamespaceMetaclass
):
    _loader_module_name = 'events'

    @classmethod
    def post_load_modules(cls):
        try:
            EventType.refresh()
        except (OperationalError, ProgrammingError):
            """
            Non fatal. Non initialized installation. Ignore exception.
            """

    def __init__(self, name, label):
        self.name = name
        self.label = label
        self.event_type_list = []
        self.__class__._registry[name] = self

    def __lt__(self, other):
        return self.label < other.label

    def __str__(self):
        return str(self.label)

    def add_event_type(self, name, label):
        event_type = EventType(namespace=self, name=name, label=label)
        self.event_type_list.append(event_type)
        return event_type

    def do_delete(self):
        self.__class__._registry.pop(self.name)

        del self

    def event_type_remove(self, event_type):
        event_type.do_delete()

    def get_event(self, name):
        return EventType.get(
            id='{}.{}'.format(self.name, name)
        )

    def get_event_types(self):
        return EventType.sort(event_type_list=self.event_type_list)


class EventType:
    _registry = {}

    @staticmethod
    def sort(event_type_list):
        return sorted(
            event_type_list, key=lambda event_type: (
                event_type.namespace.label, event_type.label
            )
        )

    @classmethod
    def all(cls):
        return EventType.sort(
            event_type_list=cls._registry.values()
        )

    @classmethod
    def get(cls, id):
        return cls._registry[id]

    @classmethod
    def get_label(cls, id):
        try:
            event_type = cls.get(id=id)
        except KeyError:
            event_type_label = TEXT_UNKNOWN_EVENT_ID % id
        else:
            event_type_label = event_type.label

        return event_type_label

    @classmethod
    def refresh(cls):
        StoredEventType = apps.get_model(
            app_label='events', model_name='StoredEventType'
        )

        event_type_list = list(
            cls.all()
        )

        stored_event_type_map = {
            stored_event_type.name: stored_event_type
            for stored_event_type in StoredEventType.objects.all()
        }

        missing_stored_event_type_list = []
        for event_type in event_type_list:
            if event_type.id not in stored_event_type_map:
                missing_stored_event_type_list.append(
                    StoredEventType(name=event_type.id)
                )

        if missing_stored_event_type_list:
            StoredEventType.objects.bulk_create(
                ignore_conflicts=True, objs=missing_stored_event_type_list
            )
            stored_event_type_map = {
                stored_event_type.name: stored_event_type
                for stored_event_type in StoredEventType.objects.all()
            }

        for event_type in event_type_list:
            stored_event_type = stored_event_type_map.get(event_type.id)

            if stored_event_type is None:
                get_or_create_result = StoredEventType.objects.get_or_create(
                    name=event_type.id
                )
                stored_event_type = get_or_create_result[0]

            event_type.stored_event_type = stored_event_type

    def __init__(self, namespace, name, label):
        self.namespace = namespace
        self.name = name
        self.label = label
        self.stored_event_type = None

        if self in self.namespace.event_type_list:
            raise EventError(
                '`EventType` "%s" already exists in parent event type '
                'namespace.', name
            )

        self.__class__._registry[self.id] = self

    def __str__(self):
        return '{}: {}'.format(self.namespace.label, self.label)

    def _commit(self, action_object=None, actor=None, target=None):
        EventSubscription = apps.get_model(
            app_label='events', model_name='EventSubscription'
        )
        Notification = apps.get_model(
            app_label='events', model_name='Notification'
        )
        ObjectEventSubscription = apps.get_model(
            app_label='events', model_name='ObjectEventSubscription'
        )
        StoredEventType = apps.get_model(
            app_label='events', model_name='StoredEventType'
        )
        User = get_user_model()

        if actor is None and target is None:
            logger.error(
                'Attempting to commit event "%s" without an actor or a '
                'target. This is not supported.', self
            )
            return

        result = action.send(
            actor or target, actor=actor, verb=self.id,
            action_object=action_object, target=target
        )[0][1]


        stored_event_type_id = StoredEventType.objects.get_pk_for_name(
            name=result.verb
        )

        if stored_event_type_id is None:
            return

        action_object_is_recorded = result.action_object_object_id is not None
        target_is_recorded = result.target_object_id is not None

        if not action_object_is_recorded and not target_is_recorded:
            return

        queryset_users = User.objects.filter(
            id__in=EventSubscription.objects.filter(
                stored_event_type_id=stored_event_type_id
            ).values('user')
        )

        if target_is_recorded:
            queryset_users = queryset_users | User.objects.filter(
                id__in=ObjectEventSubscription.objects.filter(
                    content_type_id=result.target_content_type_id,
                    object_id=target.pk,
                    stored_event_type_id=stored_event_type_id
                ).values('user')
            )

        if action_object_is_recorded:
            queryset_users = queryset_users | User.objects.filter(
                id__in=ObjectEventSubscription.objects.filter(
                    content_type_id=result.action_object_content_type_id,
                    object_id=action_object.pk,
                    stored_event_type_id=stored_event_type_id
                ).values('user')
            )

        queryset_user_id = queryset_users.values_list('pk', flat=True)

        for user_id in queryset_user_id:
            Notification.objects.create(action=result, user_id=user_id)

    def commit(self, action_object=None, actor=None, target=None):
        from .tasks import task_event_commit

        task_kwargs = {'event_id': self.id}

        if setting_disable_asynchronous_mode.value:
            self._commit(
                action_object=action_object, actor=actor, target=target
            )
        else:
            if action_object:
                task_kwargs.update(
                    {
                        'action_object_app_label': action_object._meta.app_label,
                        'action_object_model_name': action_object._meta.model_name,
                        'action_object_id': action_object.pk
                    }
                )

            if actor:
                task_kwargs.update(
                    {
                        'actor_app_label': actor._meta.app_label,
                        'actor_model_name': actor._meta.model_name,
                        'actor_id': actor.pk
                    }
                )

            if target:
                task_kwargs.update(
                    {
                        'target_app_label': target._meta.app_label,
                        'target_model_name': target._meta.model_name,
                        'target_id': target.pk
                    }
                )

            task_event_commit.apply_async(kwargs=task_kwargs)

    def do_delete(self):
        self.__class__._registry.pop(self.id)
        self.namespace.event_type_list.remove(self)

        del self

    def get_stored_event_type(self):
        if self.stored_event_type is None:
            StoredEventType = apps.get_model(
                app_label='events', model_name='StoredEventType'
            )

            self.stored_event_type, created = StoredEventType.objects.get_or_create(
                name=self.id
            )

        return self.stored_event_type

    @property
    def id(self):
        return '{}.{}'.format(self.namespace.name, self.name)


class ModelEventType:
    _inheritances = {}
    _registry = {}

    @classmethod
    def deregister_event_type(cls, event_type):
        for model, model_event_types in cls._registry.items():
            for model_event_type in model_event_types:
                if model_event_type == event_type:
                    model_event_types.remove(event_type)

    @classmethod
    def get_for_class(cls, klass):
        result = cls._registry.get(
            klass, ()
        )
        return EventType.sort(event_type_list=result)

    @classmethod
    def get_for_instance(cls, instance):
        StoredEventType = apps.get_model(
            app_label='events', model_name='StoredEventType'
        )

        events = []

        class_events = cls._registry.get(
            type(instance)
        )

        if class_events:
            events.extend(class_events)

        pks = [
            event.id for event in set(events)
        ]

        return EventType.sort(
            event_type_list=StoredEventType.objects.filter(name__in=pks)
        )

    @classmethod
    def get_inheritance(cls, model):
        return cls._inheritances[model]

    @classmethod
    def register(cls, model, event_types):
        cls._registry.setdefault(
            model, []
        )
        for event_type in event_types:
            cls._registry[model].append(event_type)

    @classmethod
    def register_inheritance(cls, model, related):
        cls._inheritances[model] = related
