import itertools
import logging

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.menus import menu_list_facet
from mayan.apps.common.utils import get_related_field

from .events import event_acl_created, event_acl_deleted, event_acl_edited
from .links import link_acl_list

logger = logging.getLogger(name=__name__)


class ModelPermission:
    _field_query_functions = {}
    _inheritances = {}
    _inheritances_reverse = {}
    _manager_names = {}
    _model_permissions = {}

    @classmethod
    def deregister(cls, model):
        cls._model_permissions.pop(model, None)

    @classmethod
    def get_inheritance_ancestor_models(cls, model):
        result = set()
        pending = [model]

        while pending:
            current = pending.pop()

            entry_list = cls._inheritances.get(
                current, ()
            )
            for entry in entry_list:
                related_model = get_related_field(
                    model=current, related_field_name=entry['field_name']
                ).related_model

                if related_model is not None and related_model not in result:
                    result.add(related_model)
                    pending.append(related_model)

        return result

    @classmethod
    def do_inheritance_cycle_check(cls, model, model_reverse, related):
        if model_reverse is None:
            return

        ancestor_models = cls.get_inheritance_ancestor_models(
            model=model_reverse
        )

        if model is model_reverse or model in ancestor_models:
            raise ImproperlyConfigured(
                'Registering inheritance from "{}" to "{}" via '
                'field "{}" would create a cycle in the ACL '
                'inheritance graph, which would cause unbounded '
                'recursion during permission resolution.'.format(
                    model.__name__, model_reverse.__name__, related
                )
            )

    @classmethod
    def get_choices_for_class(cls, klass):
        result = []

        for namespace, permissions in itertools.groupby(cls.get_for_class(klass=klass), lambda entry: entry.namespace):
            permission_options = [
                (
                    permission.pk, str(permission)
                ) for permission in permissions
            ]
            permission_options.sort(
                key=lambda entry: entry[1]
            )
            result.append(
                (namespace, permission_options)
            )

        result.sort(
            key=lambda entry: entry[0].label
        )
        return result

    @classmethod
    def get_classes(cls, as_content_type=False):
        ContentType = apps.get_model(
            app_label='contenttypes', model_name='ContentType'
        )

        if as_content_type:
            content_type_dictionary = ContentType.objects.get_for_models(
                *cls._model_permissions.keys()
            )

            content_type_ids = [
                content_type.pk for content_type in content_type_dictionary.values()
            ]

            return ContentType.objects.filter(pk__in=content_type_ids)
        else:
            return cls._model_permissions.keys()

    @classmethod
    def get_field_query_function(cls, model):
        return cls._field_query_functions[model]

    @classmethod
    def get_for_class(cls, klass):
        result = set()
        result.update(
            cls._model_permissions.get(
                klass, ()
            )
        )
        for model in cls._inheritances_reverse.get(klass, ()):
            result.update(
                cls._model_permissions.get(
                    model, ()
                )
            )

        result = list(result)
        result.sort(key=lambda permission: permission.namespace.name)

        return result

    @classmethod
    def get_for_instance(cls, instance):
        StoredPermission = apps.get_model(
            app_label='permissions', model_name='StoredPermission'
        )

        permissions = []

        class_permissions = cls.get_for_class(
            klass=type(instance)
        )

        if class_permissions:
            permissions.extend(class_permissions)

        pks = [
            permission.stored_permission.pk for permission in set(permissions)
        ]
        return StoredPermission.objects.filter(pk__in=pks)

    @classmethod
    def get_inheritances(cls, model):
        if model._meta.proxy:
            model = model._meta.proxy_for_model

        return cls._inheritances[model]

    @classmethod
    def get_manager(cls, model):
        try:
            manager_name = cls.get_manager_name(model=model)
        except KeyError:
            manager_name = None

        if manager_name:
            manager = getattr(model, manager_name)
        else:
            manager = model._meta.default_manager

        return manager

    @classmethod
    def get_manager_name(cls, model):
        return cls._manager_names[model]

    @classmethod
    def register(cls, model, permissions, bind_link=True, exclude=None):
        from django.contrib.contenttypes.fields import GenericRelation

        from mayan.apps.common.classes import ModelCopy
        from mayan.apps.events.classes import (
            EventModelRegistry, ModelEventType
        )

        AccessControlList = apps.get_model(
            app_label='acls', model_name='AccessControlList'
        )
        StoredPermission = apps.get_model(
            app_label='permissions', model_name='StoredPermission'
        )

        initalize_model_for_events = model not in cls._model_permissions
        is_excluded_subclass = issubclass(
            model, (AccessControlList, StoredPermission)
        )

        cls._model_permissions.setdefault(
            model, set()
        )

        if not is_excluded_subclass:
            try:
                cls._model_permissions[model].update(permissions)
            except TypeError as exception:
                raise ImproperlyConfigured(
                    'Make sure the permissions argument to the .register() '
                    'method is an iterable. Current value: "{}"'.format(
                        permissions
                    )
                ) from exception

        if initalize_model_for_events:

            EventModelRegistry.register(model=model)

            if not is_excluded_subclass:
                ModelEventType.register(
                    event_types=(
                        event_acl_created, event_acl_deleted,
                        event_acl_edited
                    ), model=model
                )

                if bind_link:
                    menu_list_facet.bind_links(
                        exclude=exclude, links=(link_acl_list,),
                        sources=(model,)
                    )

                model.add_to_class(
                    name='acls', value=GenericRelation(
                        to=AccessControlList, verbose_name=_(message='ACLs')
                    )
                )

                ModelCopy.add_fields_lazy(
                    model=model, field_names=('acls',)
                )

    @classmethod
    def register_field_query_function(cls, model, function):
        cls._field_query_functions[model] = function

    @classmethod
    def register_inheritance(cls, model, related, fk_field_cast=None):
        model_reverse = get_related_field(
            model=model, related_field_name=related
        ).related_model

        cls.do_inheritance_cycle_check(
            model=model, model_reverse=model_reverse, related=related
        )

        cls._inheritances_reverse.setdefault(
            model_reverse, []
        )
        cls._inheritances_reverse[model_reverse].append(model)

        cls._inheritances.setdefault(
            model, []
        )
        cls._inheritances[model].append(
            {'field_name': related, 'fk_field_cast': fk_field_cast}
        )

    @classmethod
    def register_manager(cls, model, manager_name):
        cls._manager_names[model] = manager_name
