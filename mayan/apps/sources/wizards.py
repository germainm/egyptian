from furl import furl

from django.apps import apps
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import classonlymethod
from django.utils.translation import gettext_lazy as _

from mayan.apps.forms import forms, wizards
from mayan.apps.views.view_mixins import ViewIconMixin

from .classes import DocumentCreateWizardStep
from .exceptions import SourceActionExceptionUnknown
from .icons import (
    icon_document_upload_wizard, icon_wizard_step_first,
    icon_wizard_step_next, icon_wizard_step_previous
)


class DocumentCreateWizard(ViewIconMixin, wizards.SessionWizardView):
    template_name = 'appearance/wizard.html'
    view_icon = icon_document_upload_wizard

    @classonlymethod
    def as_view(cls, *args, **kwargs):
        class EmptyForm(forms.Form):
            pass

        cls.form_list = [EmptyForm]
        return super().as_view(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        Source = apps.get_model(
            app_label='sources', model_name='Source'
        )

        form_list = DocumentCreateWizardStep.get_choices(
            attribute_name='form_class'
        )
        condition_dict = dict(
            DocumentCreateWizardStep.get_choices(attribute_name='condition')
        )

        result = self.__class__.get_initkwargs(
            condition_dict=condition_dict, form_list=form_list
        )
        self.form_list = result['form_list']
        self.condition_dict = result['condition_dict']

        for source in Source.objects.filter(enabled=True):
            try:
                action = source.get_action(name='document_upload')
                if action.has_interface(interface_name='View'):
                    return super().dispatch(request=request, *args, **kwargs)
            except SourceActionExceptionUnknown:
                """
                Non fatal. Ignore and try the next source.
                """

        messages.error(
            message=_(
                message='No interactive document sources have been defined '
                'or none have been enabled, create one before proceeding.'
            ), request=request
        )
        return HttpResponseRedirect(
            redirect_to=reverse(viewname='sources:source_list')
        )

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        wizard_step = DocumentCreateWizardStep.get(name=self.steps.current)

        context.update(
            {
                'form_css_classes': 'form-hotkey-enter form-hotkey-double-click',
                'step_title': _(
                    message='Step %(step)d of %(total_steps)d: %(step_label)s'
                ) % {
                    'step': self.steps.step1,
                    'step_label': wizard_step.label,
                    'total_steps': len(self.form_list)
                },
                'title': _(message='Document upload wizard'),
                'wizard_step': wizard_step,
                'wizard_steps': DocumentCreateWizardStep.get_all()
            }
        )

        context['form_button_overrides'] = (
            {
                'css_classes': 'btn-secondary',
                'icon': icon_wizard_step_first,
                'label': _(message='First'),
                'name_override': 'wizard_goto_step',
                'value': self.steps.first
            },
            {
                'css_classes': 'btn-secondary',
                'icon': icon_wizard_step_previous,
                'label': _(message='Previous'),
                'name_override': 'wizard_goto_step',
                'value': self.steps.prev
            },
            {
                'icon': icon_wizard_step_next,
                'is_primary': True,
                'label': _(message='Next')
            }
        )

        if not self.steps.prev:
            context['form_button_overrides'][0]['css_classes'] = 'disabled'
            context['form_button_overrides'][0]['disabled'] = True
            context['form_button_overrides'][1]['css_classes'] = 'disabled'
            context['form_button_overrides'][1]['disabled'] = True

        if not wizard_step.get_next_is_enabled(wizard=self):
            context['form_button_overrides'][2]['css_classes'] = 'disabled'
            context['form_button_overrides'][2]['disabled'] = True

        return context

    def get_form_initial(self, step):
        wizard_step = DocumentCreateWizardStep.get(name=step)

        initial = wizard_step.get_form_initial(wizard=self) or {}

        return initial

    def get_form_kwargs(self, step):
        wizard_step = DocumentCreateWizardStep.get(name=step)

        kwargs = wizard_step.get_form_kwargs(wizard=self) or {}

        return kwargs

    def done(self, form_list, **kwargs):
        query_dict = {}

        for step in DocumentCreateWizardStep.get_all():
            query_dict.update(
                step.done(wizard=self) or {}
            )

        url = furl(
            reverse(viewname='sources:document_upload')
        )
        url.args = query_dict

        return HttpResponseRedirect(
            redirect_to=url.tostr()
        )
