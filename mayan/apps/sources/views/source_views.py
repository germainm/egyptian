import logging

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.models import AccessControlList
from mayan.apps.backends.views import (
    ViewSingleObjectDynamicFormModelBackendCreate,
    ViewSingleObjectDynamicFormModelBackendEdit
)
from mayan.apps.documents.permissions import (
    permission_document_create, permission_document_file_new
)
from mayan.apps.source_periodic.source_backends.mixins import (
    SourceBackendMixinPeriodic
)
from mayan.apps.views.generics import (
    ConfirmView, FormView, MultipleObjectConfirmActionView,
    SingleObjectDeleteView, SingleObjectListView
)
from mayan.apps.views.view_mixins import (
    ExternalObjectViewMixin, ViewMixinFormSaveAndTest
)

from ..exceptions import SourceActionException
from ..forms import SourceBackendSelectionForm, SourceBackendSetupDynamicForm
from ..icons import (
    icon_source_action, icon_source_backend_selection, icon_source_create,
    icon_source_delete, icon_source_edit, icon_source_list, icon_source_test
)
from ..links import link_source_backend_selection
from ..models import Source
from ..permissions import (
    permission_sources_create, permission_sources_delete,
    permission_sources_edit, permission_sources_view
)
from ..source_backends.base import SourceBackend
from ..tasks import task_source_backend_action_execute

from .view_mixins import SourceActionViewMixin, SourceLinkNavigationViewMixin

logger = logging.getLogger(name=__name__)


class SourceActionView(
    SourceActionViewMixin, ExternalObjectViewMixin,
    SourceLinkNavigationViewMixin, MultipleObjectConfirmActionView
):
    external_object_pk_url_kwarg = 'source_id'
    external_object_queryset = Source.objects.filter(enabled=True)
    pk_url_kwarg = 'action_name'
    view_icon = icon_source_action

    def get_action_interface_kwargs(self):
        kwargs = {}
        kwargs.update(
            self.request.GET.dict()
        )
        kwargs.update(
            self.request.POST.dict()
        )
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context_super = super().get_context_data(**kwargs)

        try:
            context_action = self.object.get_confirmation_context(
                interface_name='View',
                interface_load_kwargs=self.get_action_interface_kwargs()
            )
        except SourceActionException as exception:
            messages.error(
                message=_(
                    message='Unable to execute action; %s.'
                ) % exception, request=self.request
            )
            if settings.DEBUG:
                raise
        else:
            context_super.update(**context_action)

        return context_super

    def get_object_first(self):
        action = self.external_object.get_action(
            name=self.kwargs['action_name']
        )

        action_permission = action.permission

        if action_permission:
            source_queryset = self.external_object_queryset

            queryset = AccessControlList.objects.restrict_queryset(
                permission=action_permission, queryset=source_queryset,
                user=self.request.user
            )

            get_object_or_404(
                klass=queryset, pk=self.external_object.pk
            )

        return action

    def get_object_list(self):
        self.view_mode_single = True
        self.view_mode_multiple = False

        return list(
            self.external_object.get_action_list()
        )

    def get_source_link_action(self):
        return self.get_view_source_action()

    def get_source_link_permission(self):
        if 'document_id' in self.kwargs:
            return permission_document_file_new
        else:
            return permission_document_create

    def get_source_link_queryset(self):
        return self.queryset_source_valid

    def get_source_link_view_kwargs(self):
        if 'document_id' in self.kwargs:
            return {
                'document_id': self.kwargs['document_id']
            }
        else:
            return {}

    def get_source_link_view_name(self):
        if 'document_id' in self.kwargs:
            return 'sources:document_file_upload'
        else:
            return 'sources:document_upload'

    def get_view_source_action(self):
        if 'document_id' in self.kwargs:
            return 'document_file_upload'
        else:
            return 'document_upload'

    def view_action(self):
        try:
            result = self.object.execute(
                interface_name='View',
                interface_load_kwargs=self.get_action_interface_kwargs()
            )
        except Exception as exception:
            message = _(
                message='Error processing source action; '
                '%(exception)s'
            ) % {
                'exception': exception,
            }
            logger.error(msg=message, exc_info=True)
            messages.error(
                message=message.replace('\n', ' '),
                request=self.request
            )
            if settings.DEBUG:
                raise
        else:
            messages.success(
                message=_(
                    message='Source action executed successfully.'
                ), request=self.request
            )

            return result


class SourceBackendSelectionView(FormView):
    extra_context = {
        'submit_label': _(message='Next'),
        'title': _(message='New source backend selection')
    }
    form_class = SourceBackendSelectionForm
    view_icon = icon_source_backend_selection
    view_permission = permission_sources_create

    def form_valid(self, form):
        backend = form.cleaned_data['backend']
        return HttpResponseRedirect(
            redirect_to=reverse(
                kwargs={
                    'backend_path': backend
                }, viewname='sources:source_create'
            )
        )


class SourceCreateView(ViewSingleObjectDynamicFormModelBackendCreate):
    backend_class = SourceBackend
    form_class = SourceBackendSetupDynamicForm
    post_action_redirect = reverse_lazy(viewname='sources:source_list')
    view_icon = icon_source_create
    view_permission = permission_sources_create

    def get_extra_context(self):
        backend_class = self.get_backend_class()
        return {
            'title': _(
                message='Create a "%s" source'
            ) % backend_class.label
        }

    def get_form_extra_kwargs(self):
        return {'user': self.request.user}

    def get_instance_extra_data(self):
        return {
            '_event_actor': self.request.user,
            'backend_path': self.kwargs['backend_path']
        }


class SourceDeleteView(SingleObjectDeleteView):
    model = Source
    object_permission = permission_sources_delete
    pk_url_kwarg = 'source_id'
    post_action_redirect = reverse_lazy(
        viewname='sources:source_list'
    )
    view_icon = icon_source_delete

    def get_extra_context(self):
        return {
            'object': self.object,
            'title': _(message='Delete the source: %s?') % self.object
        }


class SourceEditView(
    ViewMixinFormSaveAndTest, ViewSingleObjectDynamicFormModelBackendEdit
):
    form_class = SourceBackendSetupDynamicForm
    form_save_and_test_label = _(message='Test connection')
    model = Source
    object_permission = permission_sources_edit
    pk_url_kwarg = 'source_id'
    post_action_redirect = reverse_lazy(
        viewname='sources:source_list'
    )
    view_icon = icon_source_edit

    def get_extra_context(self):
        return {
            'title': _(message='Edit source: %s') % self.object
        }

    def get_form_extra_kwargs(self):
        return {'user': self.request.user}

    def get_form_save_and_test_available(self):
        backend_class = self.object.get_backend_class()
        return issubclass(backend_class, SourceBackendMixinPeriodic)

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}

    def view_test(self):
        task_source_backend_action_execute.apply_async(
            kwargs={
                'action_interface_kwargs': {'dry_run': True},
                'action_name': 'document_upload',
                'source_id': self.object.id,
                'user_id': self.request.user.pk
            }
        )

        messages.success(
            message=_(
                message='Source test queued. Check for newly created '
                'documents or for error log entries.'
            ), request=self.request
        )


class SourceListView(SingleObjectListView):
    model = Source
    object_permission = permission_sources_view
    view_icon = icon_source_list

    def get_extra_context(self):
        return {
            'hide_link': True,
            'hide_object': True,
            'no_results_icon': icon_source_list,
            'no_results_main_link': link_source_backend_selection.resolve(
                context=RequestContext(request=self.request)
            ),
            'no_results_text': _(
                message='Sources provide the means to upload documents. '
                'Some sources are interactive and require user input to '
                'operate. Others are automatic and run in the background '
                'without user intervention.'
            ),
            'no_results_title': _(message='No sources available'),
            'title': _(message='Sources')
        }


class SourceTestView(ExternalObjectViewMixin, ConfirmView):
    external_object_permission = permission_sources_edit
    external_object_pk_url_kwarg = 'source_id'
    external_object_class = Source
    view_icon = icon_source_test

    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request=request, *args, **kwargs)

        action_name = self.get_action_name()

        action = self.external_object.get_action(name=action_name)

        if not action.confirmation:
            messages.error(
                message=_(
                    message='The selected action "%s" does not require '
                    'confirmation and cannot be tested.'
                ) % action_name, request=self.request
            )

            previous_url = self.get_previous_url()
            return HttpResponseRedirect(redirect_to=previous_url)
        else:
            return result

    def get_action_interface_kwargs(self):
        return {'dry_run': True}

    def get_action_name(self):
        return 'document_upload'

    def get_extra_context(self):
        return {
            'object': self.external_object,
            'subtitle': _(
                message='This will execute the source code even if the '
                'source is not enabled. Sources that delete content after '
                'downloading will not do so while being tested. Check the '
                'source\'s error log for information during testing. A '
                'successful test will clear the error log.'
            ), 'title': _(
                message='Trigger check for source "%s"?'
            ) % self.external_object
        }

    def view_action(self):
        task_source_backend_action_execute.apply_async(
            kwargs={
                'action_interface_kwargs': self.get_action_interface_kwargs(),
                'action_name': self.get_action_name(),
                'source_id': self.external_object.id,
                'user_id': self.request.user.pk
            }
        )

        messages.success(
            message=_(
                message='Source test queued. Check for newly created '
                'documents or for error log entries.'
            ), request=self.request
        )
