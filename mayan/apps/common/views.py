from django.apps import apps
from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.templatetags.static import static
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView

import mayan

from mayan.apps.views.generics import ConfirmView, SimpleView
from mayan.apps.views.view_mixins import (
    ExternalContentTypeObjectViewMixin, ObjectNameViewMixin
)

from .classes import ModelCopy
from .forms import LicenseForm, TrademarkPolicyForm
from .icons import (
    icon_about, icon_egyptian_apps, icon_home, icon_license, icon_object_copy,
    icon_setup, icon_tools, icon_trademark_policy
)
from .literals import (
    EGYPTIAN_APPS, URL_EGYPTIAN_APP_FORUM, URL_EGYPTIAN_APP_STORE,
    URL_EGYPTIAN_APPS, URL_WIKI, URL_WIKI_APP
)
from .menus import menu_tools, menu_setup
from .permissions import permission_object_copy
from .settings import setting_home_view
from .utils import get_language_url


class AboutView(SimpleView):
    extra_context = {
        'title': _(message='About')
    }
    template_name = 'appearance/about.html'
    view_icon = icon_about


class EgyptianAppsView(SimpleView):
    template_name = 'common/egyptian_apps.html'
    view_icon = icon_egyptian_apps

    def get_extra_context(self):
        return {
            'egyptian_apps': [
                {
                    'installed': apps.is_installed(
                        app_name='mayan.apps.{}'.format(module)
                    ),
                    'name': name,
                    'url_documentation': get_language_url(
                        url=URL_WIKI_APP, slug=slug
                    ),
                    'url_forum': URL_EGYPTIAN_APP_FORUM.format(slug=slug),
                    'url_store': URL_EGYPTIAN_APP_STORE.format(slug=slug)
                } for module, slug, name in EGYPTIAN_APPS
            ],
            'title': _(message='Egyptian applications'),
            'url_egyptian_apps': URL_EGYPTIAN_APPS,
            'url_wiki': get_language_url(url=URL_WIKI)
        }


@method_decorator(login_not_required, name='dispatch')
class FaviconRedirectView(RedirectView):
    # Not permanent: browsers would keep the target of a former icon.
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        return static(path='appearance/images/egyptian-favicon.ico')


class HomeView(SimpleView):
    extra_context = {
        'title': _(message='Home')
    }
    template_name = 'appearance/home.html'
    view_icon = icon_home


class LicenseView(SimpleView):
    template_name = 'appearance/form_container.html'
    view_icon = icon_license

    def get_extra_context(self):
        return {
            'form': LicenseForm(),
            'read_only': True,
            'subtitle': _(
                message='%(title)s is a modified version of %(upstream)s, '
                'distributed under the same license, reproduced below. '
                '%(upstream)s: %(copyright)s. %(title)s modifications: '
                '%(fork_copyright)s.'
            ) % {
                'copyright': mayan.__copyright__,
                'fork_copyright': mayan.__fork_copyright__,
                'title': mayan.__title__,
                'upstream': mayan.__upstream_title__
            },
            'title': _(message='License')
        }


class TrademarkPolicyView(SimpleView):
    template_name = 'appearance/form_container.html'
    view_icon = icon_trademark_policy

    def get_extra_context(self):
        return {
            'form': TrademarkPolicyForm(),
            'read_only': True,
            'subtitle': _(
                message='%(upstream)s® and the %(upstream)s logo are '
                'registered trademarks of %(owner)s (U.S. Reg. No. %(word)s '
                'and %(design)s). %(title)s is a fork based on %(upstream)s: '
                'it is not affiliated with, or endorsed by, the %(upstream)s '
                'project or its trademark holder, and it does not use the '
                '%(upstream)s logo. The %(upstream)s trademark policy follows.'
            ) % {
                'design': mayan.__trademark_registration_design__,
                'owner': mayan.__author__,
                'title': mayan.__title__,
                'upstream': mayan.__upstream_title__,
                'word': mayan.__trademark_registration_word__
            },
            'title': _(message='Trademarks')
        }


class ObjectCopyView(
    ExternalContentTypeObjectViewMixin, ObjectNameViewMixin, ConfirmView
):
    external_object_permission = permission_object_copy
    view_icon = icon_object_copy

    def get_extra_context(self):
        model_copy = ModelCopy.get(model=self.external_object._meta.model)
        context = {
            'object': self.external_object,
            'submit_label': _(message='Copy'),
            'subtitle': _(message='Fields to be copied: %s') % ', '.join(
                sorted(
                    map(
                        str, model_copy.get_fields_verbose_names()
                    )
                )
            )
        }

        context['title'] = _(
            message='Make a copy of %(object_name)s "%(object)s"?'
        ) % {
            'object_name': self.get_object_name(context=context),
            'object': self.external_object
        }

        return context

    def view_action(self):
        self.external_object.copy_instance()
        messages.success(
            message=_(message='Object copied successfully.'),
            request=self.request
        )


class RootView(SimpleView):
    extra_context = {'home_view': setting_home_view.value}
    template_name = 'appearance/root.html'


class SetupListView(SimpleView):
    template_name = 'appearance/list_horizontal.html'
    view_icon = icon_setup

    def get_extra_context(self, **kwargs):
        return {
            'no_results_icon': icon_setup,
            'no_results_text': _(
                message='No results here means that don\'t have the required '
                'permissions to perform administrative task.'
            ),
            'no_results_title': _(message='No setup options available'),
            'resolved_links': menu_setup.resolve(
                request=self.request, sort_results=True
            ),
            'subtitle': _(
                message='Here you can configure all aspects of the system.'
            ),
            'title': _(message='Setup items')
        }


class ToolsListView(SimpleView):
    template_name = 'appearance/list_horizontal.html'
    view_icon = icon_tools

    def get_extra_context(self):
        return {
            'resolved_links': menu_tools.resolve(
                request=self.request, sort_results=True
            ),
            'subtitle': _(
                message='These modules are used to do system maintenance.'
            ),
            'title': _(message='Tools')
        }
