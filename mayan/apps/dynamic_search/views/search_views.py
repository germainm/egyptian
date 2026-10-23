from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import RedirectView

from mayan.apps.views.generics import (
    ConfirmView, FormView, SingleObjectListView
)
from mayan.apps.views.literals import LIST_MODE_CHOICE_ITEM
from mayan.apps.views.utils import is_url_query_positive

from ..exceptions import DynamicSearchException
from ..forms import AdvancedSearchForm, SearchForm
from ..icons import (
    icon_result_list, icon_search, icon_search_advanced,
    icon_search_backend_reindex, icon_search_submit
)
from ..links import link_search_again
from ..literals import QUERY_PARAMETER_ANY_FIELD, SEARCH_MODEL_NAME_KWARG
from ..permissions import permission_search_tools
from ..search_backends import SearchBackend
from ..settings import setting_match_all_default_value
from ..tasks import task_reindex_backend

from .view_mixins import (
    SearchModelViewMixin, SearchQueryViewMixin, SearchResultViewMixin
)


class SearchAgainView(SearchQueryViewMixin, RedirectView):
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        query_dict = self.get_search_query()

        search_term_any_field = query_dict.get(
            QUERY_PARAMETER_ANY_FIELD, ''
        ).strip()

        if search_term_any_field:
            self.pattern_name = 'search:search_simple'
        else:
            self.pattern_name = 'search:search_advanced'

        return super().get_redirect_url(*args, **kwargs)


class SearchBackendReindexView(ConfirmView):
    view_icon = icon_search_backend_reindex
    view_permission = permission_search_tools

    def get_extra_context(self):
        context = {
            'subtitle': _(
                message='This tool erases and populates the search '
                'backend\'s internal index.'
            ),
            'submit_label': _(message='Reindex'),
            'title': _(message='Reindex search backend')
        }

        search_backend_class = SearchBackend.get_class()

        if search_backend_class.feature_reindex:
            context['message'] = _(
                message='This tool is required only for some search '
                'backends. Search results will be affected while the '
                'backend is being reindexed.'
            )
        else:
            context['message'] = _(
                message='The currently selected search backend does not '
                'support or requires reindexing.'
            )

        return context

    def get_post_action_redirect(self):
        return reverse(viewname='common:tools_list')

    def view_action(self):
        task_reindex_backend.apply_async()

        messages.success(
            message=_(message='Search backend reindexing queued.'),
            request=self.request
        )


class SearchSimpleView(SearchModelViewMixin, SearchQueryViewMixin, FormView):
    template_name = 'appearance/form_container.html'
    view_icon = icon_search

    def get_extra_context(self):
        return {
            'form': self.get_form(),
            'form_action': reverse(
                kwargs={
                    SEARCH_MODEL_NAME_KWARG: self.search_model.full_name
                }, viewname='search:search_results'
            ),
            'search_model': self.search_model,
            'submit_icon': icon_search_submit,
            'submit_label': _(message='Search'),
            'submit_method': 'GET',
            'title': _(message='Search for: %s') % self.search_model.label
        }

    def get_form(self):
        query_dict = self.get_search_query()

        search_term_any_field = query_dict.get(
            QUERY_PARAMETER_ANY_FIELD, ''
        ).strip()

        if search_term_any_field:
            return SearchForm(
                initial={QUERY_PARAMETER_ANY_FIELD: search_term_any_field}
            )
        else:
            return SearchForm()


class SearchAdvancedView(SearchSimpleView):
    view_icon = icon_search_advanced

    def get_extra_context(self):
        context = super().get_extra_context()

        context.update(
            {
                'title': _(
                    message='Advanced search for: %s'
                ) % self.search_model.label
            }
        )

        return context

    def get_form(self):
        data = self.request.GET.dict()
        data['_match_all'] = data.get(
            '_match_all', setting_match_all_default_value.value
        )

        return AdvancedSearchForm(data=data, search_model=self.search_model)


class SearchResultView(
    SearchModelViewMixin, SearchResultViewMixin, SingleObjectListView
):
    view_icon = icon_result_list

    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request=request, *args, **kwargs)

        query_dict = self.get_search_query()

        query_value_save_results = query_dict.get('_save_results', 'False')

        save_results = is_url_query_positive(value=query_value_save_results)

        if save_results:
            saved_resultset, queryset = self.do_search_execute(
                store_resultset=True
            )

            if saved_resultset:
                return HttpResponseRedirect(
                    redirect_to=saved_resultset.get_absolute_url()
                )
            else:
                return result
        else:
            return result

    def get_extra_context(self):
        context = {
            'hide_object': True,
            'no_results_icon': icon_search_submit,
            'no_results_main_link': link_search_again.resolve(
                context=RequestContext(
                    dict_={
                        'search_model': self.search_model
                    }, request=self.request
                )
            ),
            'no_results_text': _(
                message='Try again using different terms.'
            ),
            'no_results_title': _(message='No search results'),
            'search_model': self.search_model,
            'subtitle': _(
                message='Search query: %s'
            ) % self.search_interpreter.to_explain(),
            'title': self.get_title()
        }

        if self.search_model.list_mode == LIST_MODE_CHOICE_ITEM:
            context['list_as_items'] = True

        return context

    def get_source_queryset(self):
        try:
            return self.get_search_queryset()
        except DynamicSearchException as exception:
            if settings.DEBUG or settings.TESTING:
                raise

            messages.error(message=exception, request=self.request)
            return self.search_model.get_queryset().none()

    def get_title(self):
        term_list = self.search_interpreter.get_term_list()

        if term_list:
            term_text = ', '.join(term_list)

            return _(
                message='Search results for: %(terms)s in %(search_model)s'
            ) % {
                'search_model': self.search_model.label, 'terms': term_text
            }
        else:
            return _(
                message='Search results for: %s'
            ) % self.search_model.label
