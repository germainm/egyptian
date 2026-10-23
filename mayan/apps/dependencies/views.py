from django.http import Http404
from django.utils.translation import gettext_lazy as _

from mayan.apps.views.generics import SimpleView, SingleObjectListView

from .classes import DependencyGroup
from .forms import DependenciesLicensesForm
from .icons import (
    icon_check_version, icon_dependency_group_list,
    icon_dependency_group_entry_detail, icon_dependency_group_entry_list,
    icon_dependency_licenses
)
from .permissions import permission_dependencies_view
from .utils import PyPIClient


class CheckVersionView(SimpleView):
    template_name = 'appearance/content_container.html'
    view_icon = icon_check_version
    view_permission = permission_dependencies_view

    def get_extra_context(self):
        return {
            'paragraphs': (
                PyPIClient().check_version_verbose(),
                _(
                    message='This process only checks the Python component of '
                    'Mayan EDMS.'
                ),
                _(
                    message='It does not verify versions of other '
                    'components like packaging or deployment technologies, '
                    'such as container or virtual machine images.'
                ),
            ),
            'title': _(message='Check for updates')
        }


class DependencyGroupEntryListView(SingleObjectListView):
    view_icon = icon_dependency_group_entry_list
    view_permission = permission_dependencies_view

    def get_extra_context(self):
        return {
            'hide_link': True,
            'hide_object': True,
            'no_results_icon': icon_dependency_group_entry_list,
            'no_results_text': _(
                message='Entries partition a dependency group into the '
                'individual sets of components it tracks.'
            ),
            'no_results_title': _(message='No entries available'),
            'object': self.get_object(),
            'subtitle': self.get_object().help_text,
            'title': _(
                message='Entries for dependency group: %s'
            ) % self.get_object()
        }

    def get_source_queryset(self):
        return self.get_object().get_entries()

    def get_object(self):
        try:
            return DependencyGroup.get(
                name=self.kwargs['dependency_group_name']
            )
        except KeyError:
            raise Http404(
                _(message='Group %s not found.') % self.kwargs[
                    'dependency_group_name'
                ]
            )


class DependencyGroupListView(SingleObjectListView):
    view_icon = icon_dependency_group_list
    view_permission = permission_dependencies_view

    def get_extra_context(self):
        return {
            'hide_link': True,
            'hide_object': True,
            'no_results_icon': icon_dependency_group_list,
            'no_results_text': _(
                message='Dependency groups organize the external components '
                'required by the system.'
            ),
            'no_results_title': _(message='No dependency groups available'),
            'title': _(message='Dependency groups')
        }

    def get_source_queryset(self):
        return DependencyGroup.get_all()


class DependencyGroupEntryDetailView(SingleObjectListView):
    view_icon = icon_dependency_group_entry_detail
    view_permission = permission_dependencies_view

    def get_extra_context(self):
        group = self.get_dependency_group()
        entry = self.get_dependency_group_entry()

        return {
            'entry': entry,
            'group': group,
            'hide_link': True,
            'hide_object': True,
            'navigation_object_list': ('group', 'entry'),
            'no_results_icon': icon_dependency_group_entry_detail,
            'no_results_text': _(
                message='Dependencies are the individual external components, '
                'such as Python or JavaScript libraries, required by the '
                'system.'
            ),
            'no_results_title': _(message='No dependencies available'),
            'title': _(
                message='Dependency group and entry: %(group)s, %(entry)s'
            ) % {
                'group': group, 'entry': entry
            }
        }

    def get_dependency_group(self):
        try:
            return DependencyGroup.get(
                name=self.kwargs['dependency_group_name']
            )
        except KeyError:
            raise Http404(
                _(message='Group %s not found.') % self.kwargs[
                    'dependency_group_name'
                ]
            )

    def get_dependency_group_entry(self):
        try:
            return self.get_dependency_group().get_entry(
                entry_name=self.kwargs['dependency_group_entry_name']
            )
        except KeyError:
            raise Http404(
                _(message='Entry %s not found.') % self.kwargs[
                    'dependency_group_entry_name'
                ]
            )

    def get_source_queryset(self):
        return self.get_dependency_group_entry().get_dependencies()


class DependencyLicensesView(SimpleView):
    template_name = 'appearance/form_container.html'
    view_icon = icon_dependency_licenses

    def get_extra_context(self):
        return {
            'form': DependenciesLicensesForm(),
            'read_only': True,
            'title': _(message='Other packages licenses')
        }
