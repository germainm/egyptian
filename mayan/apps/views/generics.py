import logging

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    FormView as DjangoFormView, DetailView, TemplateView
)
from django.views.generic.edit import (
    CreateView, DeleteView, FormMixin, UpdateView
)
from django.views.generic.list import ListView

from mayan.apps.acls.models import AccessControlList
from mayan.apps.dynamic_search.views.view_mixins import (
    SearchFilterEnabledListViewMixin
)
from mayan.apps.forms.forms import ChoiceForm

from .icons import (
    icon_add_all, icon_assign_remove_add, icon_assign_remove_remove,
    icon_confirm_form_cancel, icon_confirm_form_submit, icon_remove_all
)
from .settings import setting_paginate_by
from .view_mixins import (
    ExtraDataDeleteViewMixin, DynamicFieldSetFormViewMixin,
    ExternalObjectViewMixin, ExtraContextViewMixin, FormExtraKwargsViewMixin,
    ListModeViewMixin, ModelFormFieldsetsViewMixin, MultipleObjectViewMixin,
    ObjectActionViewMixin, ObjectNameViewMixin, RedirectionViewMixin,
    RestrictedQuerysetViewMixin, SortingViewMixin, ViewIconMixin,
    ViewMixinConfirmRemember, ViewMixinDeleteObject,
    ViewMixinFormSaveAndAddAnother, ViewMixinModalFragment,
    ViewMixinPagingArgument, ViewPermissionCheckViewMixin, ViewMixinPostAction
)

logger = logging.getLogger(name=__name__)


class MultiFormView(DjangoFormView):
    form_extra_kwargs = None
    prefix = None
    prefixes = {}
    template_name = 'appearance/form_container.html'

    def _create_form(self, form_name, klass):
        form_kwargs = self.get_form_kwargs(form_name=form_name)
        form_create_method = 'create_form__{}'.format(form_name)
        if hasattr(self, form_create_method):
            form = getattr(self, form_create_method)(**form_kwargs)
        else:
            form = klass(**form_kwargs)
        return form

    def all_forms_valid(self, forms):
        return None

    def dispatch(self, request, *args, **kwargs):
        form_classes = self.get_form_classes()
        self.forms = self.get_forms(form_classes=form_classes)
        return super().dispatch(request=request, *args, **kwargs)

    def forms_invalid(self, forms):
        return self.render_to_response(
            context=self.get_context_data(forms=forms)
        )

    def forms_valid(self, forms):
        for form_name, form in forms.items():
            form_valid_method = 'form_valid__{}'.format(form_name)

            if hasattr(self, form_valid_method):
                return getattr(self, form_valid_method)(form=form)

        self.all_forms_valid(forms=forms)

        return HttpResponseRedirect(
            redirect_to=self.get_success_url()
        )

    def get_context_data(self, **kwargs):
        if 'forms' not in kwargs:
            kwargs['forms'] = self.get_forms(
                form_classes=self.get_form_classes()
            )
        return super(FormMixin, self).get_context_data(**kwargs)

    def get_form_classes(self):
        return self.form_classes

    def get_form_extra_kwargs(self, form_name):
        method = 'get_form_extra_kwargs__{}'.format(form_name)
        if hasattr(self, method):
            func = getattr(self, method)
            return func()
        else:
            return {}

    def get_form_kwargs(self, form_name):
        kwargs = {}
        kwargs.update(
            {
                'initial': self.get_initial(form_name=form_name)
            }
        )
        kwargs.update(
            {
                'prefix': self.get_prefix(form_name=form_name)
            }
        )

        if self.request.method in ('POST', 'PUT'):
            kwargs.update(
                {
                    'data': self.request.POST,
                    'files': self.request.FILES
                }
            )

        kwargs.update(
            self.get_form_extra_kwargs(form_name=form_name) or {}
        )

        return kwargs

    def get_forms(self, form_classes):
        return {
            key: self._create_form(form_name=key, klass=klass)
            for key, klass in form_classes.items()
        }

    def get_initial(self, form_name):
        initial_method = 'get_initial__{}'.format(form_name)
        if hasattr(self, initial_method):
            func = getattr(self, initial_method)
            return func()
        else:
            return self.initial.copy()

    def get_prefix(self, form_name):
        return self.prefixes.get(form_name, self.prefix)

    def post(self, request, *args, **kwargs):
        form_list = self.forms.values()
        form_list_valid = [
            form.is_valid() for form in form_list
        ]

        if all(form_list_valid):
            return self.forms_valid(forms=self.forms)
        else:
            return self.forms_invalid(forms=self.forms)


class AddRemoveView(
    ExternalObjectViewMixin, ExtraContextViewMixin,
    ViewPermissionCheckViewMixin, RestrictedQuerysetViewMixin, ViewIconMixin,
    MultiFormView
):
    form_classes = {'form_available': ChoiceForm, 'form_added': ChoiceForm}
    template_name = 'appearance/add_remove.html'
    list_added_help_text = _(
        message='Select entries to be removed. Hold Control to select '
        'multiple entries. Once the selection is complete, click the button '
        'below or double click the list to activate the action.'
    )
    list_available_help_text = _(
        message='Select entries to be added. Hold Control to select multiple '
        'entries. Once the selection is complete, click the button below '
        'or double click the list to activate the action.'
    )

    list_added_title = None
    list_available_title = None

    main_object_model = None
    main_object_permission = None
    main_object_pk_url_kwarg = None
    main_object_pk_url_kwargs = None
    main_object_source_queryset = None

    secondary_object_model = None
    secondary_object_permission = None
    secondary_object_source_queryset = None

    main_object_method_add_name = None
    main_object_method_remove_name = None

    related_field = None

    prefixes = {'form_available': 'available', 'form_added': 'added'}

    def _action_add(self, queryset):
        kwargs = {'queryset': queryset}
        kwargs.update(
            self.get_action_add_extra_kwargs()
        )
        kwargs.update(
            self.get_actions_extra_kwargs()
        )

        if hasattr(self, 'action_add'):
            self.action_add(**kwargs)
        elif self.main_object_method_add_name:
            getattr(
                self.main_object, self.main_object_method_add_name
            )(**kwargs)
        elif self.related_field:
            getattr(
                self.main_object, self.related_field
            ).add(*queryset)
        else:
            raise ImproperlyConfigured(
                'View {} must be called with a main_object_method_add_name, '
                'a related_field, or an action_add '
                'method.'.format(self.__class__.__name__)
            )

    def _action_remove(self, queryset):
        kwargs = {'queryset': queryset}
        kwargs.update(
            self.get_action_remove_extra_kwargs()
        )
        kwargs.update(
            self.get_actions_extra_kwargs()
        )

        if hasattr(self, 'action_remove'):
            self.action_remove(**kwargs)
        elif self.main_object_method_remove_name:
            getattr(
                self.main_object, self.main_object_method_remove_name
            )(**kwargs)
        elif self.related_field:
            getattr(
                self.main_object, self.related_field
            ).remove(*queryset)
        else:
            raise ImproperlyConfigured(
                'View {} must be called with a '
                'main_object_method_remove_name, a related_field, or an '
                'action_remove method.'.format(self.__class__.__name__)
            )

    def dispatch(self, request, *args, **kwargs):
        self.external_object_class = self.main_object_model
        self.external_object_permission = self.main_object_permission
        self.external_object_pk_url_kwarg = self.main_object_pk_url_kwarg
        self.external_object_pk_url_kwargs = self.main_object_pk_url_kwargs
        self.external_object_queryset = self.get_main_object_source_queryset()

        self.main_object = self.get_external_object()
        result = super().dispatch(request=request, *args, **kwargs)
        return result

    def forms_valid(self, forms):
        selection_add = None
        selection_remove = None

        if 'available-add_all' in self.request.POST:
            selection_add = self.get_list_available_queryset()
        else:
            if 'available-selection' in self.request.POST:
                selection_add = self.get_list_available_queryset().filter(
                    pk__in=forms['form_available'].cleaned_data['selection']
                )

        if selection_add:
            self._action_add(queryset=selection_add)

        if 'added-remove_all' in self.request.POST:
            selection_remove = self.get_list_added_queryset()
        else:
            if 'added-selection' in self.request.POST:
                selection_remove = self.get_list_added_queryset().filter(
                    pk__in=forms['form_added'].cleaned_data['selection']
                )

        if selection_remove:
            self._action_remove(queryset=selection_remove)

        return super().forms_valid(forms=forms)

    def generate_choices(self, queryset):
        for obj in queryset:
            yield (
                obj.pk, str(obj)
            )

    def get_action_add_extra_kwargs(self):
        return {}

    def get_action_remove_extra_kwargs(self):
        return {}

    def get_actions_extra_kwargs(self):
        return {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'subtemplates_list': [
                    {
                        'name': 'appearance/partials/form/single.html',
                        'column_class': 'col-xs-12 col-sm-6 col-md-6 col-lg-6',
                        'context': {
                            'extra_buttons': [
                                {
                                    'icon': icon_add_all,
                                    'label': _(message='Add all'),
                                    'name': 'add_all'
                                }
                            ],
                            'form': self.forms['form_available'],
                            'hide_labels': True,
                            'submit_icon': icon_assign_remove_add,
                            'submit_label': _(message='Add'),
                            'title': self.list_available_title or ' '
                        }
                    },
                    {
                        'name': 'appearance/partials/form/single.html',
                        'column_class': 'col-xs-12 col-sm-6 col-md-6 col-lg-6',
                        'context': {
                            'extra_buttons': [
                                {
                                    'icon': icon_remove_all,
                                    'label': _(message='Remove all'),
                                    'name': 'remove_all'
                                }
                            ],
                            'form': self.forms['form_added'],
                            'hide_labels': True,
                            'submit_icon': icon_assign_remove_remove,
                            'submit_label': _(message='Remove'),
                            'title': self.list_added_title or ' '
                        }
                    }
                ]
            }
        )

        return context

    def get_disabled_choices(self):
        return ()

    def get_form_extra_kwargs(self, form_name):
        if form_name == 'form_available':
            return {
                'choices': self.generate_choices(
                    queryset=self.get_list_available_queryset()
                ),
                'help_text': self.get_list_available_help_text()
            }
        else:
            return {
                'choices': self.generate_choices(
                    queryset=self.get_list_added_queryset()
                ),
                'disabled_choices': self.get_disabled_choices(),
                'help_text': self.get_list_added_help_text()
            }

    def get_list_added_help_text(self):
        return self.list_added_help_text

    def get_list_added_queryset(self):
        if not self.related_field:
            raise ImproperlyConfigured(
                'View {} must be called with either a related_field or '
                'override .get_list_added_queryset().'.format(
                    self.__class__.__name__
                )
            )

        return self.get_secondary_object_list().filter(
            pk__in=getattr(self.main_object, self.related_field).values('pk')
        )

    def get_list_available_help_text(self):
        return self.list_available_help_text

    def get_list_available_queryset(self):
        return self.get_secondary_object_list().exclude(
            pk__in=self.get_list_added_queryset().values('pk')
        )

    def get_main_object_source_queryset(self):
        return self.main_object_source_queryset

    def get_secondary_object_list(self):
        queryset = self.get_secondary_object_source_queryset()

        if queryset is None:
            queryset = self.secondary_object_model._meta.default_manager.all()

        if self.secondary_object_permission:
            return AccessControlList.objects.restrict_queryset(
                permission=self.secondary_object_permission,
                queryset=queryset, user=self.request.user
            )
        else:
            return queryset

    def get_secondary_object_source_queryset(self):
        return self.secondary_object_source_queryset

    def get_success_url(self):
        return reverse(
            kwargs=self.request.resolver_match.kwargs,
            viewname=self.request.resolver_match.view_name
        )


class ConfirmView(
    ViewMixinModalFragment, RestrictedQuerysetViewMixin,
    ViewPermissionCheckViewMixin, ExtraContextViewMixin,
    RedirectionViewMixin, ViewIconMixin, ViewMixinConfirmRemember,
    ViewMixinPostAction, TemplateView
):
    template_name = 'appearance/confirm.html'

    def get_context_data(self, **kwargs):
        context = {
            'cancel_icon': icon_confirm_form_cancel,
            'submit_icon': icon_confirm_form_submit
        }
        context.update(
            super().get_context_data(**kwargs)
        )
        return context


class FormView(
    ViewPermissionCheckViewMixin, ExtraContextViewMixin,
    RedirectionViewMixin, FormExtraKwargsViewMixin, ViewIconMixin,
    DjangoFormView
):
    template_name = 'appearance/form_container.html'


class DynamicFormView(
    DynamicFieldSetFormViewMixin, FormView
):
    pass


class MultipleObjectFormActionView(
    ObjectActionViewMixin, RestrictedQuerysetViewMixin,
    MultipleObjectViewMixin, FormView
):
    template_name = 'appearance/form_container.html'

    def __init__(self, *args, **kwargs):
        result = super().__init__(*args, **kwargs)

        if self.__class__.mro()[0].get_queryset != MultipleObjectFormActionView.get_queryset:
            raise ImproperlyConfigured(
                '%(cls)s is overloading the `get_queryset` method. '
                'Subclasses should implement the `get_source_queryset` '
                'method instead. ' % {
                    'cls': self.__class__.__name__
                }
            )

        return result

    def form_invalid(self, form):
        if settings.DEBUG or settings.TESTING:
            logger.debug('Form invalid; %s', form.errors)

        return super().form_invalid(form=form)

    def form_valid(self, form):
        self.view_action(form=form)
        return super().form_valid(form=form)

    def get_queryset(self, **kwargs):
        try:
            return super().get_queryset(**kwargs)
        except ImproperlyConfigured:
            self.queryset = self.get_source_queryset()
            return super().get_queryset(**kwargs)


class MultipleObjectConfirmActionView(
    ViewMixinModalFragment, ExtraContextViewMixin, ObjectActionViewMixin,
    ViewPermissionCheckViewMixin, RestrictedQuerysetViewMixin,
    MultipleObjectViewMixin, RedirectionViewMixin, ViewIconMixin,
    ViewMixinConfirmRemember, ViewMixinPostAction, TemplateView
):

    template_name = 'appearance/confirm.html'

    def __init__(self, *args, **kwargs):
        result = super().__init__(*args, **kwargs)

        if self.__class__.mro()[0].get_queryset != MultipleObjectConfirmActionView.get_queryset:
            raise ImproperlyConfigured(
                '%(cls)s is overloading the `get_queryset` method. '
                'Subclasses should implement the `get_source_queryset` '
                'method instead. ' % {
                    'cls': self.__class__.__name__
                }
            )

        return result

    def get_queryset(self):
        try:
            return super().get_queryset()
        except ImproperlyConfigured:
            self.queryset = self.get_source_queryset()
            return super().get_queryset()


class RelationshipView(FormView):
    form_class = None
    model = None
    model_permission = None
    pk_url_kwarg = None
    relationship_related_field = None
    relationship_related_query_field = None
    sub_model = None
    sub_model_permission = None

    def form_valid(self, forms):
        super_result = super().form_valid(form=forms)

        try:
            for form in forms:
                form.save()
        except Exception as exception:
            messages.error(
                message=_(
                    message='Error updating relationship; %s'
                ) % exception, request=self.request
            )
            if settings.DEBUG or settings.TESTING:
                raise
        else:
            messages.success(
                message=_(message='Relationships updated successfully'),
                request=self.request
            )

        return super_result

    def get_object(self):
        queryset = AccessControlList.objects.restrict_queryset(
            permission=self.model_permission,
            queryset=self.model._meta.default_manager.all(),
            user=self.request.user
        )

        return get_object_or_404(
            klass=queryset, pk=self.kwargs[self.pk_url_kwarg]
        )

    def get_sub_model_queryset(self):
        queryset = self.sub_model.objects.all()
        return AccessControlList.objects.restrict_queryset(
            permission=self.sub_model_permission,
            queryset=queryset, user=self.request.user
        )


class SimpleView(
    ViewPermissionCheckViewMixin, ExtraContextViewMixin, ViewIconMixin,
    TemplateView
):
    pass


class SingleObjectCreateView(
    ViewMixinFormSaveAndAddAnother, ObjectNameViewMixin,
    ViewPermissionCheckViewMixin, ExtraContextViewMixin,
    RedirectionViewMixin, FormExtraKwargsViewMixin,
    ModelFormFieldsetsViewMixin, ViewIconMixin, CreateView
):
    error_message_duplicate = None
    template_name = 'appearance/form_container.html'

    def form_valid(self, form):

        self.object = form.save(commit=False)

        if hasattr(self, 'get_instance_extra_data'):
            for key, value in self.get_instance_extra_data().items():
                setattr(self.object, key, value)

        if hasattr(self, 'get_save_extra_data'):
            save_extra_data = self.get_save_extra_data()
        else:
            save_extra_data = {}

        try:
            self.object.validate_unique()
        except ValidationError as exception:
            context = self.get_context_data()

            error_message = self.get_error_message_duplicate() or _(
                message='Duplicate data error: %(error)s'
            ) % {
                'error': '\n'.join(exception.messages)
            }

            messages.error(
                message=error_message, request=self.request
            )
            return super().form_invalid(form=form)

        try:
            self.object.save(**save_extra_data)
        except Exception as exception:
            if settings.DEBUG or settings.TESTING:
                raise
            else:
                context = self.get_context_data()

                messages.error(
                    message=_(message='%(object)s not created, error: %(error)s') % {
                        'error': exception,
                        'object': self.get_object_name(context=context)
                    }, request=self.request
                )
                return super().form_invalid(form=form)
        else:
            context = self.get_context_data()

            messages.success(
                message=_(
                    message='%(object)s created successfully.'
                ) % {
                    'object': self.get_object_name(context=context)
                }, request=self.request
            )

        return HttpResponseRedirect(
            redirect_to=self.get_form_save_and_add_another_success_url()
        )

    def get_error_message_duplicate(self):
        return self.error_message_duplicate


class SingleObjectDeleteView(
    ViewMixinModalFragment, ObjectNameViewMixin, ExtraDataDeleteViewMixin,
    ViewPermissionCheckViewMixin, RestrictedQuerysetViewMixin,
    ExtraContextViewMixin, RedirectionViewMixin, ViewIconMixin,
    ViewMixinConfirmRemember, ViewMixinDeleteObject, DeleteView
):
    template_name = 'appearance/confirm.html'

    def __init__(self, *args, **kwargs):
        result = super().__init__(*args, **kwargs)

        if self.__class__.mro()[0].get_queryset != SingleObjectDeleteView.get_queryset:
            raise ImproperlyConfigured(
                '%(cls)s is overloading the `get_queryset` method. '
                'Subclasses should implement the `get_source_queryset` '
                'method instead. ' % {
                    'cls': self.__class__.__name__
                }
            )

        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {'delete_view': True}
        )
        return context

    def get_queryset(self):
        try:
            return super().get_queryset()
        except ImproperlyConfigured:
            self.queryset = self.get_source_queryset()
            return super().get_queryset()


class SingleObjectDetailView(
    ObjectNameViewMixin, ViewPermissionCheckViewMixin,
    RestrictedQuerysetViewMixin, FormExtraKwargsViewMixin,
    ExtraContextViewMixin, ModelFormFieldsetsViewMixin, ViewIconMixin,
    DetailView
):
    template_name = 'appearance/form_container.html'

    def __init__(self, *args, **kwargs):
        result = super().__init__(*args, **kwargs)

        if self.__class__.mro()[0].get_queryset != SingleObjectDetailView.get_queryset:
            raise ImproperlyConfigured(
                '%(cls)s is overloading the `get_queryset` method. '
                'Subclasses should implement the `get_source_queryset` '
                'method instead. ' % {
                    'cls': self.__class__.__name__
                }
            )

        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'read_only': True, 'form': self.get_form()
            }
        )
        return context

    def get_form(self):
        try:
            return super().get_form()
        except Exception as exception:
            if settings.DEBUG or settings.TESTING:
                raise
            else:
                messages.error(
                    message=_(
                        message='Error retrieving %(object)s; %(error)s'
                    ) % {
                        'error': exception,
                        'object': self.get_object_name(
                            context={
                                'object': self.object
                            }
                        )
                    }, request=self.request
                )

    def get_queryset(self):
        try:
            return super().get_queryset()
        except ImproperlyConfigured:
            self.queryset = self.get_source_queryset()
            return super().get_queryset()


class SingleObjectDynamicFormCreateView(
    DynamicFieldSetFormViewMixin, SingleObjectCreateView
):
    pass


class SingleObjectEditView(
    ObjectNameViewMixin, ViewPermissionCheckViewMixin,
    RestrictedQuerysetViewMixin, ExtraContextViewMixin,
    FormExtraKwargsViewMixin, RedirectionViewMixin,
    ModelFormFieldsetsViewMixin, ViewIconMixin, UpdateView
):
    template_name = 'appearance/form_container.html'

    def form_valid(self, form):

        self.object = form.save(commit=False)

        if hasattr(self, 'get_instance_extra_data'):
            for key, value in self.get_instance_extra_data().items():
                setattr(self.object, key, value)

        if hasattr(self, 'get_save_extra_data'):
            save_extra_data = self.get_save_extra_data()
        else:
            save_extra_data = {}

        context = self.get_context_data()
        object_name = self.get_object_name(context=context)

        try:
            self.object.save(**save_extra_data)
        except Exception as exception:
            if settings.DEBUG or settings.TESTING:
                raise
            else:
                messages.error(
                    message=_(
                        message='%(object)s not updated, error: %(error)s.'
                    ) % {
                        'error': exception,
                        'object': object_name
                    }, request=self.request
                )
                return super().form_invalid(form=form)
        else:
            messages.success(
                message=_(
                    message='%(object)s updated successfully.'
                ) % {
                    'object': object_name
                }, request=self.request
            )

        return HttpResponseRedirect(
            redirect_to=self.get_success_url()
        )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)

        if hasattr(self, 'get_instance_extra_data'):
            for key, value in self.get_instance_extra_data().items():
                setattr(obj, key, value)

        return obj


class SingleObjectDynamicFormEditView(
    DynamicFieldSetFormViewMixin, SingleObjectEditView
):
    pass


class SingleObjectListView(
    SortingViewMixin, ListModeViewMixin, ViewMixinPagingArgument,
    ViewPermissionCheckViewMixin, SearchFilterEnabledListViewMixin,
    RestrictedQuerysetViewMixin, ExtraContextViewMixin,
    RedirectionViewMixin, ViewIconMixin, ListView
):
    template_name = 'appearance/list.html'

    def __init__(self, *args, **kwargs):
        result = super().__init__(*args, **kwargs)

        if self.__class__.mro()[0].get_queryset != SingleObjectListView.get_queryset:
            raise ImproperlyConfigured(
                '%(cls)s is overloading the `get_queryset` method. '
                'Subclasses should implement the `get_source_queryset` '
                'method instead. ' % {
                    'cls': self.__class__.__name__
                }
            )

        return result

    def get_paginate_by(self, queryset):
        return setting_paginate_by.value

    def get_queryset(self):
        try:
            queryset = super().get_queryset()
        except ImproperlyConfigured:
            self.queryset = self.get_source_queryset()
            queryset = super().get_queryset()

        return queryset


class MultipleObjectDeleteView(MultipleObjectConfirmActionView):
    success_message_plural = _(message='%(count)d objects deleted successfully.')
    success_message_single = _(message='"%(object)s" deleted successfully.')
    success_message_singular = _(message='%(count)d object deleted successfully.')
    title_plural = _(message='Delete %(count)d objects.')
    title_single = _(message='Delete "%(object)s".')
    title_singular = _(message='Delete %(count)d object.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'delete_view': True
            }
        )

        if self.object_list.count() == 1:
            context.update(
                {
                    'object': self.object_list.first()
                }
            )

        return context

    def object_action(self, instance, form=None):
        if hasattr(self, 'get_instance_extra_data'):
            for key, value in self.get_instance_extra_data().items():
                setattr(instance, key, value)

        instance.delete()
