from functools import reduce
import logging
import operator

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import CharField, Q, Value
from django.db.models.functions import Cast, Concat
from django.utils.translation import gettext

from mayan.apps.common.utils import (
    get_related_field, resolve_attribute, return_related
)
from mayan.apps.permissions.classes import Permission
from mayan.apps.permissions.models import StoredPermission

from .classes import ModelPermission
from .events import event_acl_edited
from .exceptions import PermissionNotValidForClass

logger = logging.getLogger(name=__name__)


class AccessControlListManager(models.Manager):
    def _get_acl_filters(
        self, queryset, stored_permission, user, fk_field_cast=None,
        related_field_name=None
    ):
        result = []

        if related_field_name:
            related_field = get_related_field(
                model=queryset.model, related_field_name=related_field_name
            )

            if isinstance(related_field, GenericForeignKey):

                recursive_related_reference = '__'.join(
                    related_field_name.split('__')[0:-1]
                )

                if recursive_related_reference:
                    recursive_related_reference = '{}__'.format(
                        recursive_related_reference
                    )

                queryset_content_type_object_id = queryset.annotate(
                    ct_fk_combination=Concat(
                        '{}{}'.format(
                            recursive_related_reference,
                            related_field.ct_field
                        ), Value('-'),
                        '{}{}'.format(
                            recursive_related_reference,
                            related_field.fk_field
                        ), output_field=CharField()
                    )
                ).only('ct_fk_combination').values('ct_fk_combination')

                queryset_acl_filter = self.annotate(
                    ct_fk_combination=Concat(
                        'content_type', Value('-'), 'object_id',
                        output_field=CharField()
                    )
                ).filter(
                    permissions=stored_permission, role__groups__user=user,
                    ct_fk_combination__in=queryset_content_type_object_id
                )

                if fk_field_cast:
                    clean_acl_filter = queryset_acl_filter.annotate(
                        clean_object_id=Cast(
                            'object_id', output_field=fk_field_cast()
                        )
                    ).values_list('clean_object_id')
                else:
                    clean_acl_filter = queryset_acl_filter.values('object_id')

                field_lookup = '{}{}__in'.format(
                    recursive_related_reference, related_field.fk_field
                )
                result.append(
                    Q(
                        **{field_lookup: clean_acl_filter}
                    )
                )
            else:
                content_type = ContentType.objects.get_for_model(
                    model=related_field.related_model
                )
                field_lookup = '{}_id__in'.format(related_field_name)
                queryset_acl_filter = self.filter(
                    content_type=content_type, permissions=stored_permission,
                    role__groups__user=user
                ).values('object_id')
                if queryset_acl_filter.exists():
                    result.append(
                        Q(
                            **{field_lookup: queryset_acl_filter}
                        )
                    )

                try:
                    related_field_model_inheritances = (
                        ModelPermission.get_inheritances(
                            model=related_field.related_model
                        )
                    )
                except KeyError:
                    """
                    The related model does not inherit permissions
                    from any further model. There is nothing to
                    bubble up from this branch. Proceed to next case.
                    """
                else:
                    relation_result = []
                    for related_field_model_inheritance in related_field_model_inheritances:
                        new_related_field_name = '{}__{}'.format(
                            related_field_name, related_field_model_inheritance['field_name']
                        )
                        related_field_inherited_acl_queries = self._get_acl_filters(
                            fk_field_cast=related_field_model_inheritance['fk_field_cast'],
                            queryset=queryset,
                            stored_permission=stored_permission, user=user,
                            related_field_name=new_related_field_name
                        )
                        if related_field_inherited_acl_queries:
                            relation_result.append(
                                reduce(
                                    operator.and_,
                                    related_field_inherited_acl_queries
                                )
                            )

                    if relation_result:
                        result.append(
                            reduce(operator.or_, relation_result)
                        )
        else:
            content_type = ContentType.objects.get_for_model(
                model=queryset.model
            )
            field_lookup = 'id__in'
            queryset_acl_filter = self.filter(
                content_type=content_type, permissions=stored_permission,
                role__groups__user=user
            ).values('object_id')
            result.append(
                Q(
                    **{field_lookup: queryset_acl_filter}
                )
            )

            try:
                inheritances = (
                    ModelPermission.get_inheritances(
                        model=queryset.model
                    )
                )
            except KeyError:
                """
                Does not have inheritance entries. Proceed to next case.
                """
            else:
                relation_result = []

                for inheritance in inheritances:
                    inherited_acl_queries = self._get_acl_filters(
                        fk_field_cast=inheritance['fk_field_cast'],
                        queryset=queryset, stored_permission=stored_permission,
                        related_field_name=inheritance['field_name'],
                        user=user
                    )
                    if inherited_acl_queries:
                        relation_result.append(
                            reduce(operator.and_, inherited_acl_queries)
                        )

                if relation_result:
                    result.append(
                        reduce(operator.or_, relation_result)
                    )

            try:
                field_query_function = ModelPermission.get_field_query_function(
                    model=queryset.model
                )
            except KeyError:
                """
                Does not have specialized field query function. Proceed to
                next case.
                """
            else:
                function_results = field_query_function()

                content_type = ContentType.objects.get_for_model(
                    model=queryset.model
                )
                queryset_acl_filter = self.filter(
                    content_type=content_type, permissions=stored_permission,
                    role__groups__user=user
                ).values('object_id')

                queryset_acl = queryset.model._meta.default_manager.filter(
                    id__in=queryset_acl_filter
                ).filter(
                    **function_results['acl_filter']
                )

                if 'acl_values' in function_results:
                    queryset_acl = queryset_acl.values(
                        *function_results['acl_values']
                    )

                result.append(
                    Q(
                        **{
                            function_results['field_lookup']: queryset_acl
                        }
                    )
                )

        return result

    def check_access(self, obj, permission, user):
        if not isinstance(obj, models.Model):
            logger.debug(
                'Object "%s" of type %s is not a model instance; '
                'checking global permissions only.', str(obj),
                type(obj).__name__
            )
            Permission.check_user_permission(
                permission=permission, user=user
            )
            return True

        manager = ModelPermission.get_manager(model=obj._meta.model)
        queryset_source = manager.all()

        queryset_restricted = self.restrict_queryset(
            permission=permission, queryset=queryset_source, user=user
        )

        if queryset_restricted.filter(pk=obj.pk).exists():
            return True
        else:
            raise PermissionDenied(
                gettext(message='Insufficient access for: %s') % str(obj)
            )

    def restrict_queryset(self, permission, queryset, user):
        if not user.is_authenticated:
            return queryset.none()

        try:
            Permission.check_user_permission(
                permission=permission, user=user
            )
        except PermissionDenied:
            acl_filter_list = self._get_acl_filters(
                queryset=queryset,
                stored_permission=permission.stored_permission, user=user
            )

            if not acl_filter_list:
                return queryset.none()

            final_query = queryset.filter(
                reduce(operator.or_, acl_filter_list)
            )
            return final_query
        else:
            return queryset

    def get_inherited_permissions(self, obj, role):
        queryset_permissions_inherited = self._get_inherited_object_permissions(
            obj=obj, role=role
        )

        queryset_permission_total = (
            queryset_permissions_inherited | role.permissions.all()
        ).only('id').values('pk')

        queryset_final = ModelPermission.get_for_instance(
            instance=obj
        ).filter(pk__in=queryset_permission_total)

        return queryset_final

    def _get_inherited_object_permissions(self, obj, role, visited_types=None):
        queryset = StoredPermission.objects.none()

        if not obj:
            return queryset

        if visited_types is None:
            visited_types = set()

        visited_types.add(
            type(obj)
        )

        try:
            inheritances = ModelPermission.get_inheritances(
                model=type(obj)
            )
        except KeyError:
            """
            Does not have inheritance to other models.
            """
        else:
            for inheritance in inheritances:
                try:
                    parent_object = resolve_attribute(
                        obj=obj, attribute=inheritance['field_name']
                    )
                except AttributeError:
                    parent_object = return_related(
                        instance=obj, related_field=inheritance['field_name']
                    )

                if parent_object is None:
                    continue

                content_type = ContentType.objects.get_for_model(
                    model=parent_object
                )
                try:
                    queryset = queryset | self.get(
                        content_type=content_type,
                        object_id=parent_object.pk, role=role
                    ).permissions.all()
                except self.model.DoesNotExist:
                    """
                    No ACL exists granting this role any permission
                    on this parent object. That is the common case;
                    the parent simply contributes no inherited
                    permissions. Leave the accumulated queryset
                    unchanged and continue walking the chain.
                    """

                if type(parent_object) in visited_types:
                    continue

                queryset = queryset | self._get_inherited_object_permissions(
                    obj=parent_object, role=role,
                    visited_types=visited_types
                )

        return queryset

    def grant(self, permission, role, obj, user=None):
        class_permissions = ModelPermission.get_for_class(
            klass=obj.__class__
        )
        if permission not in class_permissions:
            raise PermissionNotValidForClass

        content_type = ContentType.objects.get_for_model(model=obj)
        acl, created = self.get_or_create(
            content_type=content_type, object_id=obj.pk,
            role=role
        )

        acl.permissions.add(permission.stored_permission)

        event_acl_edited.commit(
            action_object=obj, actor=user, target=acl
        )

        return acl

    def revoke(self, permission, role, obj, user=None):
        content_type = ContentType.objects.get_for_model(model=obj)
        acl, created = self.get_or_create(
            content_type=content_type, object_id=obj.pk,
            role=role
        )

        acl.permissions.remove(permission.stored_permission)

        if acl.permissions.exists():
            event_acl_edited.commit(
                action_object=obj, actor=user, target=acl
            )
        else:
            acl._event_actor = user
            acl.delete()
