from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.template import TemplateSyntaxError
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.views.generics import FormView
from mayan.apps.views.http import URL
from mayan.apps.views.view_mixins import (
    ContentTypeViewMixin, ExternalObjectViewMixin
)

from .classes import ModelTemplating
from .forms import TemplateSandboxForm
from .icons import icon_template_sandbox
from .permissions import permission_template_sandbox


class ObjectTemplateSandboxView(
    ContentTypeViewMixin, ExternalObjectViewMixin, FormView
):
    content_type_url_kw_args = {
        'app_label': 'app_label',
        'model_name': 'model_name'
    }
    external_object_permission = permission_template_sandbox
    external_object_pk_url_kwarg = 'object_id'
    form_class = TemplateSandboxForm
    view_icon = icon_template_sandbox

    def form_valid(self, form):
        content_type = self.get_content_type()
        path = reverse(
            kwargs={
                'app_label': content_type.app_label,
                'model_name': content_type.model,
                'object_id': self.external_object.pk
            }, viewname='templating:object_template_sandbox'
        )
        url = URL(
            path=path, query={
                'template': form.cleaned_data['template']
            }
        )

        return HttpResponseRedirect(
            redirect_to=url.to_string()
        )

    def get_external_object_queryset(self):
        return self.get_content_type().get_all_objects_for_this_type()

    def get_extra_context(self):
        return {
            'object': self.external_object,
            'previous': None,
            'submit_label': _(message='Render'),
            'title': _(
                message='Template sandbox for: %s'
            ) % self.external_object
        }

    def get_form_extra_kwargs(self):
        model_templating = self.get_model_templating()

        return {
            'model': model_templating.model,
            'model_variable': model_templating.variable_name
        }

    def get_initial(self):
        if settings.DEBUG:
            exception_list = (TemplateSyntaxError,)
        else:
            exception_list = (Exception, TemplateSyntaxError,)

        template_string = self.request.GET.get('template', '')

        try:
            result = ModelTemplating.do_render(
                obj=self.external_object, template_string=template_string
            )
        except exception_list as exception:
            result = ''
            error_message = _(
                message='Template error; %(exception)s'
            ) % {'exception': exception}

            result = error_message
        except KeyError as exception:
            raise Http404(exception)

        return {'result': result, 'template': template_string}

    def get_model_templating(self):
        model = self.external_object._meta.model
        try:
            model_templating = ModelTemplating.get_for_model(model=model)
        except KeyError as exception:
            raise Http404(exception)

        return model_templating
