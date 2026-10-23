import logging

from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.backends.views import (
    ViewSingleObjectDynamicFormModelBackendCreate,
    ViewSingleObjectDynamicFormModelBackendEdit
)
from mayan.apps.documents.models.document_type_models import DocumentType
from mayan.apps.documents.permissions import permission_document_type_edit
from mayan.apps.views.generics import (
    AddRemoveView, FormView, SingleObjectDeleteView, SingleObjectListView
)
from mayan.apps.views.view_mixins import ExternalObjectViewMixin

from .classes import SequenceBackend
from .forms import (
    SequenceBackendDynamicForm, SequenceBackendSelectionForm,
    SequenceResetForm
)
from .icons import (
    icon_document_type_sequence_list, icon_sequence_backend_selection,
    icon_sequence_create, icon_sequence_delete,
    icon_sequence_document_type_list, icon_sequence_edit, icon_sequence_list,
    icon_sequence_reset, icon_sequences
)
from .links import link_sequence_backend_selection
from .models import Sequence
from .permissions import (
    permission_sequence_create, permission_sequence_delete,
    permission_sequence_edit, permission_sequence_reset,
    permission_sequence_view
)

logger = logging.getLogger(name=__name__)


class DocumentTypeSequenceAddRemoveView(AddRemoveView):
    list_added_title = _(message='Sequences enabled')
    list_available_title = _(message='Available sequences')
    main_object_method_add_name = 'sequences_add'
    main_object_method_remove_name = 'sequences_remove'
    main_object_model = DocumentType
    main_object_permission = permission_document_type_edit
    main_object_pk_url_kwarg = 'document_type_id'
    related_field = 'sequences'
    secondary_object_model = Sequence
    secondary_object_permission = permission_sequence_edit
    view_icon = icon_document_type_sequence_list

    def get_actions_extra_kwargs(self):
        return {'user': self.request.user}

    def get_extra_context(self):
        return {
            'object': self.main_object,
            'title': _(
                message='Sequences to enable for document type: %s'
            ) % self.main_object
        }


class SequenceBackendSelectionView(FormView):
    extra_context = {
        'submit_label': _(message='Next'),
        'title': _(message='New sequence backend selection')
    }
    form_class = SequenceBackendSelectionForm
    view_icon = icon_sequence_backend_selection
    view_permission = permission_sequence_create

    def form_valid(self, form):
        backend = form.cleaned_data['backend']

        return HttpResponseRedirect(
            redirect_to=reverse(
                kwargs={'backend_path': backend},
                viewname='sequences:sequence_create'
            )
        )


class SequenceCreateView(ViewSingleObjectDynamicFormModelBackendCreate):
    backend_class = SequenceBackend
    form_class = SequenceBackendDynamicForm
    post_action_redirect = reverse_lazy(
        viewname='sequences:sequence_list'
    )
    view_icon = icon_sequence_create
    view_permission = permission_sequence_create

    def get_extra_context(self):
        backend_class = self.get_backend_class()

        return {
            'title': _(message='Create a "%s" sequence') % backend_class.label
        }

    def get_instance_extra_data(self):
        return {
            '_event_actor': self.request.user,
            'backend_path': self.kwargs['backend_path']
        }


class SequenceDeleteView(SingleObjectDeleteView):
    model = Sequence
    object_permission = permission_sequence_delete
    pk_url_kwarg = 'sequence_id'
    post_action_redirect = reverse_lazy(
        viewname='sequences:sequence_list'
    )
    view_icon = icon_sequence_delete

    def get_extra_context(self):
        return {
            'title': _(message='Delete sequence: %s') % self.object
        }


class SequenceDocumentTypeAddRemoveView(AddRemoveView):
    list_added_title = _(message='Document types enabled')
    list_available_title = _(message='Available document types')
    main_object_method_add_name = 'document_types_add'
    main_object_method_remove_name = 'document_types_remove'
    main_object_model = Sequence
    main_object_permission = permission_sequence_edit
    main_object_pk_url_kwarg = 'sequence_id'
    related_field = 'document_types'
    secondary_object_model = DocumentType
    secondary_object_permission = permission_document_type_edit
    view_icon = icon_sequence_document_type_list

    def get_actions_extra_kwargs(self):
        return {'user': self.request.user}

    def get_extra_context(self):
        return {
            'object': self.main_object,
            'title': _(
                message='Document types allowed to use sequence: %s'
            ) % self.main_object
        }


class SequenceEditView(ViewSingleObjectDynamicFormModelBackendEdit):
    form_class = SequenceBackendDynamicForm
    model = Sequence
    object_permission = permission_sequence_edit
    pk_url_kwarg = 'sequence_id'
    view_icon = icon_sequence_edit

    def get_extra_context(self):
        return {
            'title': _(message='Edit sequence: %s') % self.object
        }

    def get_instance_extra_data(self):
        return {'_event_actor': self.request.user}


class SequenceListView(SingleObjectListView):
    model = Sequence
    object_permission = permission_sequence_view
    view_icon = icon_sequence_list

    def get_extra_context(self):
        return {
            'hide_object': True,
            'no_results_icon': icon_sequences,
            'no_results_main_link': link_sequence_backend_selection.resolve(
                context=RequestContext(request=self.request)
            ),
            'no_results_text': _(
                message='Sequences produce the next value of a numbering '
                'scheme. The scheme itself is provided by a backend, which '
                'means increments, symbols, and limits are expressed in '
                'code rather than in template markup.'
            ),
            'no_results_title': _(message='No sequences available'),
            'title': _(message='Sequences')
        }


class SequenceResetView(ExternalObjectViewMixin, FormView):
    external_object_class = Sequence
    external_object_permission = permission_sequence_reset
    external_object_pk_url_kwarg = 'sequence_id'
    form_class = SequenceResetForm
    view_icon = icon_sequence_reset

    def form_valid(self, form):
        self.external_object.do_reset(
            position=form.cleaned_data['position'], user=self.request.user
        )

        return HttpResponseRedirect(
            redirect_to=self.get_success_url()
        )

    def get_extra_context(self):
        return {
            'object': self.external_object,
            'subtitle': _(
                message='Setting the position of a sequence that is already '
                'in use can produce values that were issued before. Use this '
                'to seed a sequence from the system it replaces.'
            ),
            'submit_label': _(message='Reset'),
            'title': _(
                message='Reset sequence: %s'
            ) % self.external_object
        }

    def get_initial(self):
        return {'position': self.external_object.position}

    def get_success_url(self):
        return reverse(viewname='sequences:sequence_list')
