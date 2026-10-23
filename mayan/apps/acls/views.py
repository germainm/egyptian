import logging

from django.template import RequestContext
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from mayan.apps.permissions.models import Role
from mayan.apps.views.generics import (
    AddRemoveView, SingleObjectCreateView, SingleObjectDeleteView,
    SingleObjectListView
)
from mayan.apps.views.view_mixins import (
    ContentTypeViewMixin, ExternalObjectViewMixin
)

from .classes import ModelPermission
from .forms import ACLCreateForm
from .icons import (
    icon_acl_create, icon_acl_delete, icon_acl_list, icon_acl_permissions,
    icon_global_acl_list
)
from .links import link_acl_create
from .literals import TEXT_ACL_NO_RESULTS
from .models import AccessControlList, GlobalAccessControlListProxy
from .permissions import permission_acl_edit, permission_acl_view

logger = logging.getLogger(name=__name__)


class ACLCreateView(
    ContentTypeViewMixin, ExternalObjectViewMixin, SingleObjectCreateView
):
    content_type_url_kw_args = {
        'app_label': 'app_label',
        'model_name': 'model_name'
    }
    external_object_permission = permission_acl_edit
    external_object_pk_url_kwarg = 'object_id'
    form_class = ACLCreateForm
    view_icon = icon_acl_create

    def get_error_message_duplicate(self):
        return _(
            message='An ACL for "%(object)s" using role "%(role)s" already exists. '
            'Edit that ACL entry instead.'
        ) % {
            'object': self.get_external_object(), 'role': self.object.role
        }

    def get_external_object_queryset(self):
        return self.get_content_type().get_all_objects_for_this_type()

    def get_extra_context(self):
        return {
            'object': self.external_object,
            'title': _(
                message='New access control lists for: %s'
            ) % self.external_object
        }

    def get_form_extra_kwargs(self):
        try:
            roles = self.external_object.acls.values('role')
        except AttributeError:
            roles = Role.objects.none()

        return {
            'field_name': 'role',
            'label': _(message='Role'),
            'queryset': Role.objects.exclude(pk__in=roles),
            'widget_attributes': {'class': 'select2'},
            'user': self.request.user
        }

    def get_instance_extra_data(self):
        return {
            '_event_actor': self.request.user,
            'content_object': self.external_object
        }

    def get_queryset(self):
        return self.external_object.acls.all()

    def get_success_url(self):
        return self.object.get_absolute_url()


class ACLDeleteView(SingleObjectDeleteView):
    model = AccessControlList
    object_permission = permission_acl_edit
    pk_url_kwarg = 'acl_id'
    view_icon = icon_acl_delete

    def get_extra_context(self):
        return {
            'acl': self.object,
            'navigation_object_list': ('object', 'acl'),
            'object': self.object.content_object,
            'title': _(message='Delete ACL: %s') % self.object
        }

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}

    def get_post_action_redirect(self):
        return reverse(
            kwargs={
                'app_label': self.object.content_type.app_label,
                'model_name': self.object.content_type.model,
                'object_id': self.object.object_id
            }, viewname='acls:acl_list'
        )


class ACLListView(
    ContentTypeViewMixin, ExternalObjectViewMixin, SingleObjectListView
):
    content_type_url_kw_args = {
        'app_label': 'app_label',
        'model_name': 'model_name'
    }
    external_object_permission = permission_acl_view
    external_object_pk_url_kwarg = 'object_id'
    view_icon = icon_acl_list

    def get_external_object_queryset(self):
        return self.get_content_type().get_all_objects_for_this_type()

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_acl_list,
            'no_results_main_link': link_acl_create.resolve(
                context=RequestContext(
                    self.request, {
                        'resolved_object': self.external_object
                    }
                )
            ),
            'no_results_title': _(
                message='There are no ACLs for this object'
            ),
            'no_results_text': TEXT_ACL_NO_RESULTS,
            'object': self.external_object,
            'title': _(
                message='Access control lists for: %s'
            ) % self.external_object
        }

    def get_source_queryset(self):
        return self.external_object.acls.all()


class ACLPermissionAddRemoveView(AddRemoveView):
    list_added_title = _(message='Granted permissions')
    list_available_title = _(message='Available permissions')
    main_object_method_add_name = 'permissions_add'
    main_object_method_remove_name = 'permissions_remove'
    main_object_model = AccessControlList
    main_object_permission = permission_acl_edit
    main_object_pk_url_kwarg = 'acl_id'
    related_field = 'permissions'
    view_icon = icon_acl_permissions

    def generate_choices(self, queryset):
        namespaces_dictionary = {}

        object_list = sorted(
            queryset,
            key=lambda permission: permission.volatile_permission.label
        )

        for permission in object_list:
            namespaces_dictionary.setdefault(
                permission.volatile_permission.namespace.label, []
            )
            namespaces_dictionary[
                permission.volatile_permission.namespace.label
            ].append(
                (
                    permission.pk, force_str(s=permission)
                )
            )

        return sorted(
            namespaces_dictionary.items()
        )

    def get_actions_extra_kwargs(self):
        return {'user': self.request.user}

    def get_disabled_choices(self):
        return self.main_object.get_inherited_permissions().values_list(
            'pk', flat=True
        )

    def get_extra_context(self):
        return {
            'acl': self.main_object,
            'object': self.main_object.content_object,
            'navigation_object_list': ('object', 'acl'),
            'title': _(
                message='Role "%(role)s" permission\'s for "%(object)s".'
            ) % {
                'object': self.main_object.content_object,
                'role': self.main_object.role
            }
        }

    def get_list_added_help_text(self):
        if self.main_object.get_inherited_permissions():
            return _(
                message='Disabled permissions are inherited from a parent '
                'object or directly granted to the role and can\'t be '
                'removed from this view. Inherited permissions need to be '
                'removed from the parent object\'s ACL or from them role via '
                'the Setup menu.'
            )
        else:
            return super().get_list_added_help_text()

    def get_list_added_queryset(self):
        queryset_acl = super().get_list_added_queryset()

        return (
            queryset_acl | self.main_object.get_inherited_permissions()
        ).distinct()

    def get_secondary_object_source_queryset(self):
        return ModelPermission.get_for_instance(
            instance=self.main_object.content_object
        )


class GlobalACLListView(SingleObjectListView):
    model = GlobalAccessControlListProxy
    object_permission = permission_acl_view
    view_icon = icon_global_acl_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_acl_list,
            'no_results_title': _(message='There are no ACLs'),
            'no_results_text': TEXT_ACL_NO_RESULTS,
            'title': _(message='Global access control lists')
        }
