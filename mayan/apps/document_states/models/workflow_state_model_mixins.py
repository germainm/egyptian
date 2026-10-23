import hashlib

from django.conf import settings
from django.core import serializers
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.models import AccessControlList
from mayan.apps.documents.models.document_models import Document
from mayan.apps.documents.permissions import permission_document_view

from ..literals import (
    ERROR_LOG_DOMAIN_NAME, GRAPHVIZ_COLOR_STATE_FILL_FINAL,
    GRAPHVIZ_COLOR_STATE_FILL_INITIAL, GRAPHVIZ_COLOR_STATE_FONT_COLOR_FINAL,
    GRAPHVIZ_ID_STATE, GRAPHVIZ_SHAPE_CIRCLE, GRAPHVIZ_SHAPE_DOUBLECIRCLE,
    GRAPHVIZ_STYLE_FILLED, WORKFLOW_ACTION_ON_ENTRY, WORKFLOW_ACTION_ON_EXIT
)


class WorkflowStateBusinessLogicMixin:
    def do_active_set(self, log_entry):
        queryset = self.entry_actions.filter(enabled=True)
        self.do_queryset_actions_execute(
            log_entry=log_entry, queryset=queryset
        )

    def do_active_unset(self, log_entry):
        queryset = self.exit_actions.filter(enabled=True)
        self.do_queryset_actions_execute(
            log_entry=log_entry, queryset=queryset
        )

    def do_queryset_actions_execute(self, queryset, log_entry):
        workflow_instance = log_entry.workflow_instance

        for action in queryset:
            context = workflow_instance.get_context()
            context.update(
                {'action': action, 'log_entry': log_entry}
            )

            try:
                action.execute(
                    context=context, workflow_instance=workflow_instance
                )
            except Exception as exception:
                error_log_text = _(
                    message='Error executing workflow action "%(action)s"; '
                    '%(exception)s'
                ) % {'action': action, 'exception': exception}

                workflow_instance.document.create(
                    domain_name=ERROR_LOG_DOMAIN_NAME, text=error_log_text
                )

                if settings.DEBUG or settings.TESTING:
                    raise

                break

    def do_diagram_generate(self, diagram):
        fill_color = ''
        font_color = ''
        style = ''

        is_edge_state = self.initial or not self.destination_transitions.exists() or not self.origin_transitions.exists()

        if is_edge_state:
            shape = GRAPHVIZ_SHAPE_DOUBLECIRCLE
        else:
            shape = GRAPHVIZ_SHAPE_CIRCLE

        if self.final:
            fill_color = GRAPHVIZ_COLOR_STATE_FILL_FINAL
            font_color = GRAPHVIZ_COLOR_STATE_FONT_COLOR_FINAL
            style = GRAPHVIZ_STYLE_FILLED
        elif self.initial:
            fill_color = GRAPHVIZ_COLOR_STATE_FILL_INITIAL
            style = GRAPHVIZ_STYLE_FILLED

        node_kwargs = {
            'fillcolor': fill_color,
            'fontcolor': font_color,
            'label': self.label,
            'name': self.get_graph_id(),
            'shape': shape,
            'style': style
        }
        diagram.node(**node_kwargs)

        for action in self.actions.all():
            action.do_diagram_generate(diagram=diagram)

        for escalation in self.escalations.all():
            escalation.do_diagram_generate(diagram=diagram)

    @property
    def entry_actions(self):
        return self.actions.filter(when=WORKFLOW_ACTION_ON_ENTRY)

    @property
    def exit_actions(self):
        return self.actions.filter(when=WORKFLOW_ACTION_ON_EXIT)

    def get_actions_display(self):
        field_list = [
            str(field) for field in self.actions.all()
        ]
        field_list.sort()

        return ', '.join(field_list)

    get_actions_display.short_description = _(message='Actions')

    def get_escalations_display(self):
        field_list = [
            str(field) for field in self.escalations.all()
        ]
        field_list.sort()

        return ', '.join(field_list)

    get_escalations_display.short_description = _(message='Escalations')

    def get_graph_id(self):
        return '{}{}'.format(GRAPHVIZ_ID_STATE, self.pk)

    def get_hash(self):
        result = hashlib.sha256(
            string=serializers.serialize(
                format='json', queryset=(self,)
            ).encode()
        )

        for action in self.actions.all():
            result.update(
                action.get_hash().encode()
            )

        for escalation in self.escalations.all():
            result.update(
                escalation.get_hash().encode()
            )

        return result.hexdigest()


class WorkflowStateRuntimeProxyBusinessLogicMixin:
    def get_documents(self, permission=None, user=None):
        if self.workflow.ignore_completed:
            queryset = Document.valid.none()
        else:
            queryset = Document.valid.filter(workflows__state_active=self)

        if permission and user:
            queryset = AccessControlList.objects.restrict_queryset(
                permission=permission, queryset=queryset,
                user=user
            )

        return queryset

    def get_document_count(self, user):
        return self.get_documents(
            permission=permission_document_view, user=user
        ).count()
