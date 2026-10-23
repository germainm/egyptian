from django.http import Http404

from django.utils.translation import gettext_lazy as _

from mayan.apps.views.generics import SingleObjectListView

from ..icons import icon_search_model_detail, icon_search_model_list
from ..search_models import SearchModel


class SearchModelListView(SingleObjectListView):
    extra_context = {
        'hide_link': True,
        'hide_object': True,
        'no_results_icon': icon_search_model_list,
        'no_results_text': _(
            message='Search models expose the app data that can be searched.'
        ),
        'no_results_title': _(message='No search models available'),
        'title': _(message='Search models')
    }
    view_icon = icon_search_model_list

    def get_source_queryset(self):
        return SearchModel.all()


class SearchModelSearchFieldListView(SingleObjectListView):
    view_icon = icon_search_model_detail

    def get_extra_context(self):
        search_model = self.get_search_model()

        return {
            'hide_link': True,
            'hide_object': True,
            'no_results_icon': icon_search_model_detail,
            'no_results_text': _(
                message='Search fields are the individual attributes of a '
                'search model that can be queried.'
            ),
            'no_results_title': _(message='No search fields available'),
            'object': search_model,
            'title': _(
                message='Fields for search model: %s'
            ) % search_model.label
        }

    def get_search_model(self):
        try:
            return SearchModel.get(
                name=self.kwargs['search_model_name']
            )
        except KeyError:
            raise Http404(
                _(message='Search model: %s, not found') % self.kwargs[
                    'search_model_name'
                ]
            )

    def get_source_queryset(self):
        search_model = self.get_search_model()
        return search_model.search_fields_label_sorted
