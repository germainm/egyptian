from django.utils.translation import gettext_lazy as _

from mayan.apps.views.generics import SingleObjectListView
from mayan.apps.views.view_mixins import ContentTypeViewMixin

from .classes import ModelProperty, ModelWrapper
from .icons import icon_model_property_list, icon_property_model_list


class ModelPropertyListView(ContentTypeViewMixin, SingleObjectListView):
    content_type_url_kw_args = {
        'app_label': 'app_label',
        'model_name': 'model_name'
    }
    view_icon = icon_model_property_list

    def get_extra_context(self):
        model = self.get_model()
        verbose_name = model._meta.verbose_name

        model_wrapper = ModelWrapper(model=model)

        return {
            'hide_link': True,
            'hide_object': True,
            'no_results_icon': self.view_icon,
            'no_results_title': _(message='No properties available'),
            'object': model_wrapper,
            'title': _(message='Properties for model: %s') % verbose_name
        }

    def get_model(self):
        content_type = self.get_content_type()
        return content_type.model_class()

    def get_source_queryset(self):
        model = self.get_model()

        result = list(
            ModelProperty.get_for(model=model)
        )
        return result


class PropertyModelListView(SingleObjectListView):
    extra_context = {
        'hide_link': True,
        'hide_object': True,
        'no_results_icon': icon_property_model_list,
        'no_results_text': _(
            message='Properties expose computed or descriptive attributes '
            'of a model for use in other parts of the system.'
        ),
        'no_results_title': _(
            message='No models with registered properties'
        ),
        'title': _(message='Models with registered properties')
    }
    view_icon = icon_property_model_list

    def get_source_queryset(self):
        result = ModelWrapper.all()
        return result
