from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.views.generics import (
    AddRemoveView, MultipleObjectDeleteView, SingleObjectCreateView,
    SingleObjectDetailView, SingleObjectEditView, SingleObjectListView
)
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from ..icons import (
    icon_current_user_detail, icon_user_create, icon_user_delete_single,
    icon_user_edit, icon_user_group_list, icon_user_set_options,
    icon_user_setup, icon_user_list
)
from ..links import link_user_create
from ..literals import FIELDS_ALL, FIELDSETS_ALL, FIELDSETS_USER
from ..permissions import (
    permission_group_edit, permission_user_create, permission_user_delete,
    permission_user_edit, permission_user_view
)
from ..querysets import get_user_queryset

from .view_mixins import DynamicUserFormFieldViewMixin


class UserCreateView(SingleObjectCreateView):
    extra_context = {
        'title': _(message='Create new user')
    }
    fields = FIELDS_ALL
    fieldsets = FIELDSETS_ALL
    form_save_and_add_another_disabled = True
    model = get_user_model()
    view_icon = icon_user_create
    view_permission = permission_user_create

    def form_valid(self, form):
        super().form_valid(form=form)
        return HttpResponseRedirect(
            redirect_to=reverse(
                kwargs={
                    'user_id': self.object.pk
                }, viewname='authentication:user_set_password'
            )
        )

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class UserDeleteView(MultipleObjectDeleteView):
    error_message = _(
        message='Error deleting user "%(instance)s"; %(exception)s'
    )
    object_permission = permission_user_delete
    pk_url_kwarg = 'user_id'
    post_action_redirect = reverse_lazy(
        viewname='user_management:user_list'
    )
    success_message_plural = _(
        message='%(count)d users deleted successfully.'
    )
    success_message_single = _(
        message='User "%(object)s" deleted successfully.'
    )
    success_message_singular = _(
        message='%(count)d user deleted successfully.'
    )
    title_plural = _(message='Delete the %(count)d selected users.')
    title_single = _(message='Delete user: %(object)s.')
    title_singular = _(message='Delete the %(count)d selected user.')
    view_icon = icon_user_delete_single

    def get_extra_context(self, **kwargs):
        if self.request.user in self.object_list:
            return {
                'message': _(
                    message='Warning! You are about to delete your own user '
                    'account. You will lose access to the system. This '
                    'process is not reversible.'
                )
            }
        else:
            return {}

    def get_source_queryset(self):
        return get_user_queryset(user=self.request.user)


class UserDetailView(DynamicUserFormFieldViewMixin, SingleObjectDetailView):
    object_permission = permission_user_view
    pk_url_kwarg = 'user_id'
    view_icon = icon_current_user_detail

    def get_extra_context(self, **kwargs):
        return {
            'object': self.object,
            'title': _(message='Details of user: %s') % self.object
        }

    def get_source_queryset(self):
        return get_user_queryset(user=self.request.user)


class UserEditView(DynamicUserFormFieldViewMixin, SingleObjectEditView):
    fieldsets = FIELDSETS_USER
    object_permission = permission_user_edit
    pk_url_kwarg = 'user_id'
    post_action_redirect = reverse_lazy(
        viewname='user_management:user_list'
    )
    view_icon = icon_user_edit

    def get_extra_context(self):
        return {
            'object': self.object,
            'title': _(message='Edit user: %s') % self.object
        }

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}

    def get_source_queryset(self):
        return get_user_queryset(user=self.request.user)


class UserGroupAddRemoveView(AddRemoveView):
    list_available_title = _(message='Available groups')
    list_added_title = _(message='User groups')
    main_object_method_add_name = 'groups_add'
    main_object_method_remove_name = 'groups_remove'
    main_object_permission = permission_user_edit
    main_object_pk_url_kwarg = 'user_id'
    secondary_object_model = Group
    secondary_object_permission = permission_group_edit
    view_icon = icon_user_group_list

    def get_actions_extra_kwargs(self):
        return {'user': self.request.user}

    def get_extra_context(self):
        return {
            'object': self.main_object,
            'title': _(message='Groups of user: %s') % self.main_object
        }

    def get_list_added_queryset(self):
        return self.main_object.get_groups(
            permission=permission_group_edit, user=self.request.user
        )

    def get_main_object_source_queryset(self):
        return get_user_queryset(user=self.request.user)


class UserListView(SingleObjectListView):
    object_permission = permission_user_view
    view_icon = icon_user_list

    def get_extra_context(self):
        return {
            'hide_link': True,
            'hide_object': True,
            'no_results_icon': icon_user_setup,
            'no_results_main_link': link_user_create.resolve(
                context=RequestContext(request=self.request)
            ),
            'no_results_text': _(
                message='User accounts can be created from this view. After '
                'creating a user account you will be prompted to set a '
                'password for it.'
            ),
            'no_results_title': _(message='There are no user accounts'),
            'title': _(message='Users')
        }

    def get_source_queryset(self):
        return get_user_queryset(user=self.request.user)


class UserOptionsEditView(ExternalObjectViewMixin, SingleObjectEditView):
    external_object_permission = permission_user_edit
    external_object_pk_url_kwarg = 'user_id'
    fields = ('block_password_change',)
    view_icon = icon_user_set_options

    def get_external_object_queryset(self):
        return get_user_queryset(user=self.request.user)

    def get_extra_context(self):
        return {
            'title': _(
                message='Edit options for user: %s'
            ) % self.external_object,
            'object': self.external_object
        }

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}

    def get_object(self):
        return self.external_object.user_options

    def get_post_action_redirect(self):
        return reverse(viewname='user_management:user_list')
