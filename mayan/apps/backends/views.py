from mayan.apps.views.generics import (
    SingleObjectDynamicFormCreateView, SingleObjectDynamicFormEditView
)

from .view_mixins import ViewMixinDynamicFormBackendClass, ViewMixinURLBackend


class ViewSingleObjectDynamicFormModelBackendCreate(
    ViewMixinDynamicFormBackendClass, ViewMixinURLBackend,
    SingleObjectDynamicFormCreateView
):
    pass


class ViewSingleObjectDynamicFormModelBackendEdit(
    ViewMixinDynamicFormBackendClass, SingleObjectDynamicFormEditView
):
    def get_backend_class(self):
        return self.object.get_backend_class()
