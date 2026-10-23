from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db.models.query import QuerySet
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.cache import patch_vary_headers
from django.utils.translation import gettext_lazy as _, ngettext
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import DeleteView, ModelFormMixin

from mayan.apps.acls.classes import ModelPermission
from mayan.apps.acls.models import AccessControlList
from mayan.apps.common.settings import setting_home_view
from mayan.apps.databases.utils import check_queryset
from mayan.apps.forms import form_mixins, forms
from mayan.apps.permissions.classes import Permission

from .exceptions import ActionError
from .http import URL
from .literals import (
    PK_LIST_KEY, PK_LIST_SEPARATOR, HEADER_NAME_MODAL,
    HEADER_NAME_PAGE_RELOAD, LIST_MODE_CHOICE_ITEM, LIST_MODE_CHOICE_LIST,
    MODAL_FRAGMENT_ENABLED, TEXT_LIST_AS_ITEMS_PARAMETER,
    TEXT_LIST_AS_ITEMS_VARIABLE_NAME, TEXT_MODAL_PARAMETER,
    TEXT_MODAL_VARIABLE_NAME, TEXT_SORT_FIELD_PARAMETER,
    TEXT_SORT_FIELD_VARIABLE_NAME, REDIRECT_STATUS_CODES
)
from .models import UserConfirmView, UserViewMode
from .settings import (
    setting_object_list_display_limit, setting_paging_argument
)
from .utils import (
    get_request_referer, get_safe_redirect_url, is_url_query_positive
)


class ContentTypeViewMixin:
    content_type_url_kw_args = {
        'app_label': 'app_label',
        'model_name': 'model_name'
    }

    def get_content_type(self):
        return get_object_or_404(
            klass=ContentType,
            app_label=self.kwargs[
                self.content_type_url_kw_args['app_label']
            ],
            model=self.kwargs[
                self.content_type_url_kw_args['model_name']
            ]
        )


class ExtraDataDeleteViewMixin:
    def form_valid(self, form):
        if hasattr(self, 'get_instance_extra_data'):
            for key, value in self.get_instance_extra_data().items():
                setattr(self.object, key, value)

        return super().form_valid(form=form)


class DynamicFormViewMixin:
    form_class = forms.DynamicForm

    def get_form_kwargs(self):
        data = super().get_form_kwargs()
        data.update(
            {
                'schema': self.get_form_schema()
            }
        )
        return data


class DynamicFieldSetFormViewMixin(DynamicFormViewMixin):
    def get_form_class(self):
        form_class = super().get_form_class()
        form_class.fieldsets = self.get_form_fieldsets()
        return form_class

    def get_form_fieldsets(self):
        return None


class ExternalObjectBaseMixin:
    external_object_class = None
    external_object_permission = None
    external_object_pk_url_kwarg = 'pk'
    external_object_pk_url_kwargs = None
    external_object_queryset = None

    def get_pk_url_kwargs(self):
        pk_url_kwargs = {}

        if self.external_object_pk_url_kwargs:
            pk_url_kwargs = self.external_object_pk_url_kwargs
        else:
            pk_url_kwargs['pk'] = self.external_object_pk_url_kwarg

        result = {}
        for key, value in pk_url_kwargs.items():
            result[key] = self.kwargs[value]

        return result

    def get_external_object(self, queryset=None):
        return get_object_or_404(
            klass=queryset or self.get_external_object_queryset_filtered(),
            **self.get_pk_url_kwargs()
        )

    def get_external_object_permission(self):
        return self.external_object_permission

    def get_external_object_queryset(self):
        if self.external_object_queryset is not None:
            queryset = self.external_object_queryset
            if isinstance(queryset, QuerySet):
                queryset = queryset.all()
        elif self.external_object_class is not None:
            manager = ModelPermission.get_manager(
                model=self.external_object_class
            )
            queryset = manager.all()
        else:
            raise ImproperlyConfigured(
                'View `{}` must provide either an '
                '`external_object_queryset`, an `external_object_class` or '
                'a custom `get_external_object_queryset` method.'.format(
                    self.__class__.__name__
                )
            )

        return check_queryset(view=self, queryset=queryset)

    def get_external_object_queryset_filtered(self):
        queryset = self.get_external_object_queryset()
        permission = self.get_external_object_permission()

        if permission:
            queryset = AccessControlList.objects.restrict_queryset(
                permission=permission, queryset=queryset,
                user=self.request.user
            )

        return queryset


class ExternalObjectViewMixin(ExternalObjectBaseMixin):
    def dispatch(self, request, *args, **kwargs):
        self.external_object = self.get_external_object()
        return super().dispatch(request=request, *args, **kwargs)


class ExternalContentTypeObjectViewMixin(
    ContentTypeViewMixin, ExternalObjectViewMixin
):
    external_object_pk_url_kwarg = 'object_id'

    def get_external_object_queryset(self):
        self.external_object_content_type = self.get_content_type()
        self.external_object_class = self.external_object_content_type.model_class()
        return super().get_external_object_queryset()


class ExtraContextViewMixin:
    extra_context = {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            self.get_extra_context()
        )
        return context

    def get_extra_context(self):
        return self.extra_context


class FormExtraKwargsViewMixin:
    form_extra_kwargs = {}

    def get_form_extra_kwargs(self):
        return self.form_extra_kwargs

    def get_form_kwargs(self):
        result = super().get_form_kwargs()
        result.update(
            self.get_form_extra_kwargs()
        )
        return result


class ViewMixinFormSaveAndAddAnother:
    form_save_and_add_another_button_label = _(message='Create and add another')
    form_save_and_add_another_button_name = 'save_and_add_another'
    form_save_and_add_another_disabled = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        button_disabled = self.get_form_save_and_add_another_disabled()
        if not button_disabled:
            extra_buttons = list(
                context.get('extra_buttons') or ()
            )
            button_label = self.get_form_save_and_add_another_button_label()
            button_name = self.get_form_save_and_add_another_button_name()
            extra_buttons.append(
                {
                    'label': button_label,
                    'name': button_name
                }
            )
            context['extra_buttons'] = extra_buttons

        return context

    def get_form_save_and_add_another_button_label(self):
        return self.form_save_and_add_another_button_label

    def get_form_save_and_add_another_button_name(self):
        return self.form_save_and_add_another_button_name

    def get_form_save_and_add_another_disabled(self):
        return self.form_save_and_add_another_disabled

    def get_form_save_and_add_another_success_url(self):
        button_name = self.get_form_save_and_add_another_button_name()
        button_used = button_name in self.request.POST

        button_disabled = self.get_form_save_and_add_another_disabled()
        if not button_disabled and button_used:
            return self.request.get_full_path()

        return self.get_success_url()


class ViewMixinFormSaveAndTest:
    form_save_and_test_button_name = 'save_and_test'
    form_save_and_test_label = None

    def get_form_save_and_test_available(self):
        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.get_form_save_and_test_available():
            extra_buttons = list(
                context.get('extra_buttons') or ()
            )
            extra_buttons.append(
                {
                    'label': self.form_save_and_test_label,
                    'name': self.form_save_and_test_button_name
                }
            )
            context['extra_buttons'] = extra_buttons

        return context

    def form_valid(self, form):
        result = super().form_valid(form=form)

        test_requested = self.form_save_and_test_button_name in self.request.POST
        save_succeeded = isinstance(result, HttpResponseRedirect)

        if test_requested and save_succeeded and self.get_form_save_and_test_available():
            self.view_test()
            return HttpResponseRedirect(
                redirect_to=self.request.get_full_path()
            )

        return result

    def view_test(self):
        raise NotImplementedError(
            'Subclasses must implement the `view_test` method.'
        )


class ListModeViewMixin:
    list_mode_fixed = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.list_mode_fixed:
            context.update(
                {
                    'hide_list_mode_toggle': True,
                }
            )
            final_list_mode = LIST_MODE_CHOICE_ITEM
        else:
            if context.get(TEXT_LIST_AS_ITEMS_VARIABLE_NAME):
                default_mode = LIST_MODE_CHOICE_ITEM
            else:
                default_mode = LIST_MODE_CHOICE_LIST

            user_list_mode = self.request.GET.get(TEXT_LIST_AS_ITEMS_PARAMETER)

            resolver_match = self.request.resolver_match

            view_name = '{}:{}'.format(
                resolver_match.namespace, resolver_match.url_name
            )

            if user_list_mode:
                UserViewMode.objects.update_or_create(
                    defaults={
                        'namespace': resolver_match.namespace,
                        'value': user_list_mode
                    }, name=view_name, user=self.request.user
                )
                final_list_mode = user_list_mode
            else:
                user_view_mode, created = UserViewMode.objects.get_or_create(
                    defaults={
                        'namespace': resolver_match.namespace,
                        'value': default_mode
                    }, name=view_name, user=self.request.user
                )
                final_list_mode = user_view_mode.value

        context.update(
            {
                TEXT_LIST_AS_ITEMS_VARIABLE_NAME: final_list_mode == LIST_MODE_CHOICE_ITEM
            }
        )
        return context


class ModelFormFieldsetsViewMixin(ModelFormMixin):
    fields = None

    def get_form_class(self):
        form_class = super().get_form_class()

        if form_mixins.FormMixinFieldsets in form_class.mro():
            return form_class
        else:
            class FormFieldsetForm(form_mixins.FormMixinFieldsets, form_class):
                pass

            FormFieldsetForm.fieldsets = getattr(self, 'fieldsets', None)
            return FormFieldsetForm


class MultipleExternalObjectViewMixin(ExternalObjectBaseMixin):
    def dispatch(self, request, *args, **kwargs):
        self.external_object_list = self.get_external_object_list()
        if self.view_mode_single:
            self.external_object = self.external_object_list.first()

        return super().dispatch(request=request, *args, **kwargs)

    def get_external_object_list(self):
        self.view_mode_single = False
        self.view_mode_multiple = False

        pk_url_kwarg = self.external_object_pk_url_kwarg
        pk = self.kwargs.get(pk_url_kwarg)
        pk_list = self.get_pk_list()

        if pk is not None:
            id_list = (pk,)
            self.view_mode_single = True

        if pk_list is not None:
            id_list = pk_list
            self.view_mode_multiple = True

        return self.get_external_object_queryset_filtered().filter(
            pk__in=id_list
        )


class MultipleObjectViewMixin(SingleObjectMixin):
    pk_list_key = PK_LIST_KEY
    pk_list_separator = PK_LIST_SEPARATOR

    def dispatch(self, request, *args, **kwargs):
        self.object_list = self.get_object_list()
        if self.view_mode_single:
            self.object = self.get_object_first()

        return super().dispatch(request=request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return super(SingleObjectMixin, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super(SingleObjectMixin, self).get_context_data(**kwargs)

    def get_object(self):
        raise AttributeError

    def get_object_first(self):
        return self.object_list.first()

    def get_object_list(self, queryset=None):
        self.view_mode_multiple = False
        self.view_mode_single = False

        if queryset is None:
            queryset = self.get_queryset()

        pk = self.kwargs.get(self.pk_url_kwarg)
        slug = self.kwargs.get(self.slug_url_kwarg)
        pk_list = self.get_pk_list()

        if pk is not None:
            queryset = queryset.filter(pk=pk)
            self.view_mode_single = True

        if slug is not None and (pk is None or self.query_pk_and_slug):
            slug_field = self.get_slug_field()
            queryset = queryset.filter(
                **{slug_field: slug}
            )
            self.view_mode_single = True

        if pk_list is not None:
            queryset = queryset.filter(pk__in=pk_list)
            self.view_mode_multiple = True

        if pk is None and slug is None and pk_list is None:
            raise AttributeError(
                'View %s must be called with '
                'either an object pk, a slug or an pk list.'
                % self.__class__.__name__
            )

        try:
            queryset.get()
        except queryset.model.MultipleObjectsReturned:
            return queryset
        except queryset.model.DoesNotExist:
            raise Http404(
                _(message='No %(verbose_name)s found matching the query') %
                {'verbose_name': queryset.model._meta.verbose_name}
            )
        else:
            return queryset

    def get_pk_list(self):
        result = self.request.GET.get(
            self.pk_list_key, self.request.POST.get(self.pk_list_key)
        )

        if result:
            return result.split(self.pk_list_separator)
        else:
            return None


class ObjectActionViewMixin:
    error_message = _(
        message='Unable to perform operation on object %(instance)s; %(exception)s.'
    )
    object_list_display_limit = None
    post_object_action_url = None
    success_message_plural = _(
        message='Operation performed on %(count)d objects.'
    )
    success_message_single = _(message='Operation performed on %(object)s.')
    success_message_singular = _(
        message='Operation performed on %(count)d object.'
    )
    title_plural = _(message='Perform operation on %(count)d objects.')
    title_single = _(message='Perform operation on %(object)s.')
    title_singular = _(message='Perform operation on %(count)d object.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'title' not in context:
            title = None

            if self.view_mode_single:
                title = self.title_single % {'object': self.object}
            elif self.view_mode_multiple:
                object_list_count = self.get_object_list_count()

                title = ngettext(
                    singular=self.title_singular,
                    plural=self.title_plural, number=object_list_count
                ) % {
                    'count': object_list_count
                }

            context['title'] = title

        context.update(
            {
                'object_list_display': self.get_object_list_display(),
                'object_list_display_excess_count': self.get_object_list_display_excess_count
            }
        )

        return context

    def get_object_list_count(self):
        try:
            result = self._object_list_count
        except AttributeError:
            result = self.object_list.count()
            self._object_list_count = result

        return result

    def get_object_list_display(self):
        limit = self.get_object_list_display_limit()

        if limit < 1:
            return ()

        if not self.view_mode_multiple:
            return ()

        return self.object_list[:limit]

    def get_object_list_display_excess_count(self):
        limit = self.get_object_list_display_limit()

        if limit < 1:
            return 0

        excess_count = self.get_object_list_count() - limit

        return max(excess_count, 0)

    def get_object_list_display_limit(self):
        if self.object_list_display_limit is None:
            return setting_object_list_display_limit.value
        else:
            return self.object_list_display_limit

    def get_post_object_action_url(self):
        return self.post_object_action_url

    def get_success_message(self, count):
        if self.view_mode_single:
            return self.success_message_single % {'object': self.object}

        if self.view_mode_multiple:
            return ngettext(
                singular=self.success_message_singular,
                plural=self.success_message_plural,
                number=count
            ) % {
                'count': count
            }

    def object_action(self, instance, form=None):
        raise NotImplementedError

    def view_action(self, form=None):
        self.action_count = 0
        self.action_id_list = []

        for instance in self.object_list:
            try:
                self.object_action(form=form, instance=instance)
            except ActionError as exception:
                messages.error(
                    message=self.error_message % {
                        'exception': exception, 'instance': instance
                    }, request=self.request
                )
            else:
                self.action_count += 1
                self.action_id_list.append(instance.pk)

        messages.success(
            message=self.get_success_message(count=self.action_count),
            request=self.request
        )

        success_url = self.get_post_object_action_url()
        if success_url:
            self.success_url = success_url


class ObjectNameViewMixin:
    def get_object_name(self, context=None):
        if not context:
            context = self.get_context_data()

        object_name = context.get('object_name')

        if not object_name:
            view_object = getattr(
                self, 'object', context['object']
            )
            try:
                object_name = view_object._meta.verbose_name
            except AttributeError:
                object_name = _(message='Object')

        return object_name


class RedirectionViewMixin:
    action_cancel_redirect = None
    next_url = None
    post_action_redirect = None
    previous_url = None
    success_url = None

    def get_action_cancel_redirect(self):
        return self.action_cancel_redirect

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'next': self.get_next_url(),
                'previous': self.get_previous_url()
            }
        )

        return context

    def get_post_action_redirect(self):
        return self.post_action_redirect

    def get_destination_url(self, argument_name, view_url):
        url_home = reverse(setting_home_view.value)

        url_referer = get_safe_redirect_url(
            default_url=url_home, request=self.request,
            url=get_request_referer(default=url_home, request=self.request)
        )

        url_view = get_safe_redirect_url(
            default_url=url_referer, request=self.request, url=view_url
        )

        url_requested = self.request.POST.get(
            argument_name, self.request.GET.get(argument_name, None)
        )

        return get_safe_redirect_url(
            default_url=url_view, request=self.request, url=url_requested
        )

    def get_next_url(self):
        if self.next_url:
            return self.next_url
        else:
            view_url = self.get_post_action_redirect()
            return self.get_destination_url(
                argument_name='next', view_url=view_url
            )

    def get_previous_url(self):
        if self.previous_url:
            return self.previous_url
        else:
            view_url = self.get_action_cancel_redirect()
            return self.get_destination_url(
                argument_name='previous', view_url=view_url
            )

    def get_success_url(self):
        return self.success_url or self.get_next_url() or self.get_previous_url()


class RedirectWithPageReloadViewMixin:
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request=request, *args, **kwargs)

        status_code = getattr(response, 'status_code', None)

        if status_code in REDIRECT_STATUS_CODES:
            if self.get_page_reload_enabled():
                response[HEADER_NAME_PAGE_RELOAD] = 'true'

        return response

    def get_page_reload_enabled(self):
        return True


class ViewMixinModalFragment:
    modal_fragment_disabled = False
    template_name_modal = 'appearance/confirm_modal.html'

    @classmethod
    def get_modal_fragment_capable(cls):
        return MODAL_FRAGMENT_ENABLED and not cls.modal_fragment_disabled

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request=request, *args, **kwargs)

        if request.method == 'GET' and self.get_modal_fragment_capable():
            patch_vary_headers(
                response=response, newheaders=(HEADER_NAME_MODAL,)
            )

            if self.get_modal_fragment_requested():
                if getattr(response, 'status_code', None) == 200:
                    response[HEADER_NAME_MODAL] = 'true'

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.get_modal_fragment_capable() and self.get_modal_fragment_requested():
            context.update(
                {
                    TEXT_MODAL_VARIABLE_NAME: True,
                    'modal_form_action': self.get_modal_form_action()
                }
            )

        return context

    def get_modal_form_action(self):
        query = self.request.GET.copy()
        query.pop(TEXT_MODAL_PARAMETER, None)

        url = URL(
            path=self.request.path, query_string=query.urlencode()
        )
        return url.to_string()

    def get_modal_fragment_requested(self):
        modal_query = is_url_query_positive(
            value=self.request.GET.get(TEXT_MODAL_PARAMETER)
        )
        modal_header = self.request.headers.get(
            HEADER_NAME_MODAL
        ) == 'true'

        return bool(modal_query or modal_header)

    def get_template_names(self):
        if self.request.method == 'GET':
            if self.get_modal_fragment_capable() and self.get_modal_fragment_requested():
                return [self.template_name_modal]

        return super().get_template_names()


class RestrictedQuerysetViewMixin:
    model = None
    object_permission = None
    source_queryset = None

    def get_object_permission(self):
        return self.object_permission

    def get_queryset(self, source_queryset=None):
        queryset = source_queryset or self.get_source_queryset()
        object_permission = self.get_object_permission()

        if object_permission:
            queryset = AccessControlList.objects.restrict_queryset(
                permission=object_permission, queryset=queryset,
                user=self.request.user
            )

        return queryset

    def get_source_queryset(self):
        if self.source_queryset is None:
            if self.model:
                return self.model._default_manager.all()
            else:
                raise ImproperlyConfigured(
                    '%(cls)s is missing a QuerySet. Define '
                    '%(cls)s.model, %(cls)s.source_queryset, or override '
                    '%(cls)s.get_source_queryset().' % {
                        'cls': self.__class__.__name__
                    }
                )

        return self.source_queryset.all()


class SortingViewMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                TEXT_SORT_FIELD_VARIABLE_NAME: self.get_sort_fields()
            }
        )
        return context

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)

        sort_fields = self.get_sort_fields()
        if sort_fields:
            queryset = queryset.order_by(
                *sort_fields.split(',')
            )

        return queryset

    def get_sort_fields(self):
        return self.request.GET.get(TEXT_SORT_FIELD_PARAMETER)


class ViewIconMixin:
    view_icon = None

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        view_icon = self.get_view_icon()
        if view_icon:
            context['view_icon'] = view_icon

        return context

    def get_view_icon(self):
        return self.view_icon


class ViewMixinConfirmRemember:
    def get(self, request, *args, **kwargs):
        resolver_match = request.resolver_match

        view_name = '{}:{}'.format(
            resolver_match.namespace, resolver_match.url_name
        )

        ask_again_raw = request.GET.get('ask_again')

        ask_again = is_url_query_positive(value=ask_again_raw)

        if ask_again:
            remember = False
        else:
            try:
                confirm_view = UserConfirmView.objects.get(
                    namespace=resolver_match.namespace, name=view_name,
                    user=self.request.user
                )
            except UserConfirmView.DoesNotExist:
                remember = False
            else:
                remember = confirm_view.remember

        if isinstance(self, DeleteView):
            if remember:
                self.object = self.get_object()

                form = self.get_form()
                return super().form_valid(form=form)
            else:
                return super().get(request=request, *args, **kwargs)
        else:
            if remember:
                redirect_to = self.get_success_url()

                self.view_action()
                return HttpResponseRedirect(redirect_to=redirect_to)
            else:
                return super().get(request=request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        resolver_match = request.resolver_match

        view_name = '{}:{}'.format(
            resolver_match.namespace, resolver_match.url_name
        )

        remember_raw = request.POST.get('remember')

        remember = is_url_query_positive(value=remember_raw)

        if remember is None:
            remember = False

        confirm_view, created = UserConfirmView.objects.update_or_create(
            defaults={
                'namespace': resolver_match.namespace,
                'remember': remember
            }, name=view_name, user=self.request.user
        )

        return super().post(request=request, *args, **kwargs)


class ViewMixinDeleteObject:
    def form_valid(self, form):
        context = self.get_context_data()
        object_name = self.get_object_name(context=context)

        try:
            result = super().form_valid(form=form)
        except Exception as exception:
            messages.error(
                message=_(
                    message='%(object)s not deleted, error: %(error)s.'
                ) % {
                    'error': exception,
                    'object': object_name
                }, request=self.request
            )
            raise
        else:
            messages.success(
                message=_(
                    message='%(object)s deleted successfully.'
                ) % {
                    'object': object_name
                }, request=self.request
            )

            return result


class ViewMixinExternalObjectOwnerPlusFilteredQueryset:
    def get_external_object_queryset(self):
        queryset = super().get_external_object_queryset()
        queryset_user = queryset.filter(user=self.request.user)

        if self.external_object_optional_permission:
            queryset = queryset_user | AccessControlList.objects.restrict_queryset(
                permission=self.external_object_optional_permission, queryset=queryset,
                user=self.request.user
            )
        else:
            queryset = queryset_user

        return queryset.distinct()


class ViewMixinOwnerPlusFilteredQueryset:
    def get_source_queryset(self):
        queryset = super().get_source_queryset()
        queryset_user = queryset.filter(user=self.request.user)

        if self.object_optional_permission:
            queryset = queryset_user | AccessControlList.objects.restrict_queryset(
                permission=self.object_optional_permission, queryset=queryset,
                user=self.request.user
            )
        else:
            queryset = queryset_user

        return queryset.distinct()


class ViewMixinPagingArgument:
    @property
    def page_kwarg(self):
        return setting_paging_argument.value


class ViewMixinPostAction:
    def post(self, request, *args, **kwargs):
        self.view_action()

        redirect_to = self.get_success_url()

        return HttpResponseRedirect(redirect_to=redirect_to)


class ViewPermissionCheckViewMixin:
    view_permission = None

    def dispatch(self, request, *args, **kwargs):
        view_permission = self.get_view_permission()
        if view_permission:
            Permission.check_user_permission(
                permission=view_permission, user=self.request.user
            )

        return super().dispatch(request=request, *args, **kwargs)

    def get_view_permission(self):
        return self.view_permission
