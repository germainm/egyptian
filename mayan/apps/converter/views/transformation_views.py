import logging

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.views.generics import (
    FormView, MultipleObjectDeleteView, SingleObjectCreateView,
    SingleObjectEditView, SingleObjectListView
)
from mayan.apps.views.view_mixins import ExternalContentTypeObjectViewMixin

from ..forms import LayerTransformationSelectForm
from ..icons import (
    icon_transformation_create, icon_transformation_delete,
    icon_transformation_edit, icon_transformation_list,
    icon_transformation_select
)
from ..links import link_transformation_select
from ..models import ObjectLayer
from ..transformations import BaseTransformation

from .view_mixins import (
    ViewMixinDynamicTransformationFormClass, ViewMixinLayer,
    ViewMixinTransformationTemplateName
)

logger = logging.getLogger(name=__name__)


class TransformationCreateView(
    ViewMixinDynamicTransformationFormClass, ViewMixinLayer,
    ExternalContentTypeObjectViewMixin, ViewMixinTransformationTemplateName,
    SingleObjectCreateView
):
    view_icon = icon_transformation_create

    def form_valid(self, form):
        object_layer, created = ObjectLayer.objects.get_for(
            layer=self.layer, obj=self.external_object
        )

        instance = form.save(commit=False)
        instance.content_object = self.external_object
        instance.name = self.kwargs['transformation_name']
        instance.object_layer = object_layer

        try:
            instance.full_clean()
            instance.save()
        except Exception as exception:
            logger.debug('Invalid form, exception: %s', exception)
            messages.error(
                message=_(
                    message='Error creating transformation: %s.'
                ) % exception, request=self.request
            )
            return super().form_invalid(form=form)
        else:
            return super().form_valid(form=form)

    def get_extra_context(self):
        transformation_template_name = self.get_transformation_template_name()

        if transformation_template_name:
            form_field_css_classes = 'd-none'
        else:
            form_field_css_classes = ''

        return {
            'content_object': self.external_object,
            'form_field_css_classes': form_field_css_classes,
            'layer': self.layer,
            'layer_name': self.layer.name,
            'navigation_object_list': ('content_object',),
            'title': _(
                message='Create layer "%(layer)s" transformation '
                '"%(transformation)s" for: %(object)s'
            ) % {
                'layer': self.layer,
                'transformation': self.get_transformation_class(),
                'object': self.external_object
            }
        }

    def get_form_extra_kwargs(self):
        return {
            'initial': {'order': None},
            'transformation_name': self.kwargs['transformation_name']
        }

    def get_external_object_permission(self):
        return self.layer.get_permission(action='create')

    def get_post_action_redirect(self):
        return reverse(
            kwargs={
                'app_label': self.kwargs['app_label'],
                'model_name': self.kwargs['model_name'],
                'object_id': self.kwargs['object_id'],
                'layer_name': self.kwargs['layer_name']
            }, viewname='converter:transformation_list'
        )

    def get_transformation_class(self):
        return BaseTransformation.get(
            name=self.kwargs['transformation_name']
        )


class TransformationDeleteView(
    ViewMixinLayer, ExternalContentTypeObjectViewMixin,
    MultipleObjectDeleteView
):
    pk_url_kwarg = 'transformation_id'
    success_message_plural = _(message='%(count)d transformations deleted successfully.')
    success_message_single = _(
        message='Transformation "%(object)s" deleted successfully.'
    )
    success_message_singular = _(
        message='%(count)d transformation deleted successfully.'
    )
    title_plural = _(message='Delete the %(count)d selected transformations')
    title_single = _(message='Delete transformation: %(object)s')
    title_singular = _(message='Delete the %(count)d selected transformation')
    view_icon = icon_transformation_delete

    def get_external_object_permission(self):
        return self.layer.get_permission(action='delete')

    def get_extra_context(self):
        return {
            'content_object': self.external_object,
            'layer': self.layer,
            'layer_name': self.layer.name,
            'navigation_object_list': ('content_object', 'transformation'),
            'previous': self.get_post_action_redirect(),
        }

    def get_post_action_redirect(self):
        obj = self.object_list.first()

        return reverse(
            kwargs={
                'app_label': obj.object_layer.content_type.app_label,
                'model_name': obj.object_layer.content_type.model,
                'object_id': obj.object_layer.object_id,
                'layer_name': obj.object_layer.stored_layer.name
            }, viewname='converter:transformation_list'
        )

    def get_source_queryset(self):
        return self.layer.get_transformations_for(
            obj=self.external_object
        )


class TransformationEditView(
    ViewMixinLayer, ViewMixinDynamicTransformationFormClass,
    ExternalContentTypeObjectViewMixin, ViewMixinTransformationTemplateName,
    SingleObjectEditView
):
    pk_url_kwarg = 'transformation_id'
    view_icon = icon_transformation_edit

    def form_valid(self, form):
        instance = form.save(commit=False)
        try:
            instance.full_clean()
            instance.save()
        except Exception as exception:
            logger.debug('Invalid form, exception: %s', exception)
            return super().form_invalid(form=form)
        else:
            return super().form_valid(form=form)

    def get_external_object_permission(self):
        return self.layer.get_permission(action='edit')

    def get_extra_context(self):
        transformation_template_name = self.get_transformation_template_name()

        if transformation_template_name:
            form_field_css_classes = 'd-none'
        else:
            form_field_css_classes = ''

        return {
            'content_object': self.external_object,
            'form_field_css_classes': form_field_css_classes,
            'layer': self.layer,
            'layer_name': self.layer.name,
            'navigation_object_list': ('content_object', 'transformation'),
            'title': _(
                message='Edit transformation "%(transformation)s" '
                'for: %(content_object)s'
            ) % {
                'transformation': self.object,
                'content_object': self.external_object
            },
            'transformation': self.object
        }

    def get_post_action_redirect(self):
        return reverse(
            kwargs={
                'app_label': self.object.object_layer.content_type.app_label,
                'model_name': self.object.object_layer.content_type.model,
                'object_id': self.object.object_layer.object_id,
                'layer_name': self.object.object_layer.stored_layer.name
            }, viewname='converter:transformation_list'
        )

    def get_source_queryset(self):
        return self.layer.get_transformations_for(
            obj=self.external_object
        )

    def get_transformation_class(self):
        return self.object.get_transformation_class()


class TransformationListView(
    ViewMixinLayer, ExternalContentTypeObjectViewMixin, SingleObjectListView
):
    view_icon = icon_transformation_list

    def get_external_object_permission(self):
        return self.layer.get_permission(action='view')

    def get_extra_context(self):
        return {
            'content_object': self.external_object,
            'hide_link': True,
            'hide_object': True,
            'layer': self.layer,
            'layer_name': self.layer.name,
            'navigation_disable_menus_link_group_object_header': True,
            'navigation_object_list': ('content_object',),
            'no_results_icon': self.layer.icon,
            'no_results_main_link': link_transformation_select.resolve(
                context=RequestContext(
                    dict_={
                        'resolved_object': self.external_object,
                        'layer_name': self.kwargs['layer_name'],
                    }, request=self.request
                )
            ),
            'no_results_text': self.layer.get_empty_results_text(),
            'no_results_title': _(
                message='There are no entries for layer "%(layer_name)s"'
            ) % {'layer_name': self.layer.label},
            'title': _(
                message='Layer "%(layer)s" transformations for: %(object)s'
            ) % {
                'layer': self.layer,
                'object': self.external_object
            }
        }

    def get_source_queryset(self):
        return self.layer.get_transformations_for(obj=self.external_object)


class TransformationSelectView(
    ViewMixinLayer, ExternalContentTypeObjectViewMixin, FormView
):
    form_class = LayerTransformationSelectForm
    template_name = 'appearance/form_container.html'
    view_icon = icon_transformation_select

    def form_valid(self, form):
        transformation_class = BaseTransformation.get(
            name=form.cleaned_data['transformation']
        )
        if transformation_class.arguments:
            return HttpResponseRedirect(
                redirect_to=reverse(
                    kwargs={
                        'app_label': self.kwargs['app_label'],
                        'model_name': self.kwargs['model_name'],
                        'object_id': self.kwargs['object_id'],
                        'layer_name': self.kwargs['layer_name'],
                        'transformation_name': form.cleaned_data[
                            'transformation'
                        ]
                    }, viewname='converter:transformation_create'
                )
            )
        else:
            object_layer, created = ObjectLayer.objects.get_for(
                obj=self.external_object, layer=self.layer
            )
            object_layer.transformations.create(
                name=form.cleaned_data['transformation']
            )

            messages.success(
                message=_(message='Transformation created successfully.'),
                request=self.request
            )

            return HttpResponseRedirect(
                redirect_to=reverse(
                    kwargs={
                        'app_label': self.kwargs['app_label'],
                        'model_name': self.kwargs['model_name'],
                        'object_id': self.kwargs['object_id'],
                        'layer_name': self.kwargs['layer_name']
                    }, viewname='converter:transformation_list'
                )
            )

    def get_external_object_permission(self):
        return self.layer.get_permission(action='select')

    def get_extra_context(self):
        return {
            'content_object': self.external_object,
            'layer': self.layer,
            'layer_name': self.kwargs['layer_name'],
            'navigation_object_list': ('content_object',),
            'submit_label': _(message='Select'),
            'title': _(
                message='Select new layer "%(layer)s" transformation '
                'for: %(object)s'
            ) % {
                'layer': self.layer,
                'object': self.external_object
            }
        }

    def get_form_extra_kwargs(self):
        return {'layer': self.layer}
