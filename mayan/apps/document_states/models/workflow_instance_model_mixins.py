import datetime
import json
import logging

from django.apps import apps
from django.conf import settings
from django.utils.timezone import now

from mayan.apps.acls.models import AccessControlList

from ..permissions import permission_workflow_instance_transition

logger = logging.getLogger(name=__name__)


class WorkflowInstanceBusinessLogicMixin:
    def do_check_escalation(self):
        current_state = self.get_current_state()

        if not current_state.final and not self.workflow.ignore_completed:
            for escalation in current_state.escalations.filter(enabled=True):
                kwargs = {escalation.unit: escalation.amount}
                timedelta = datetime.timedelta(**kwargs)

                expiration_datetime = self.get_last_log_entry_datetime() + timedelta

                if now() > expiration_datetime:
                    condition_context = {'workflow_instance': self}

                    condition_result = escalation.evaluate_condition(
                        context=condition_context
                    )
                    if condition_result:
                        escalation_comment = escalation.get_comment()

                        self.do_transition(
                            comment=escalation_comment,
                            transition=escalation.transition
                        )

    def do_context_update(self, context):
        workflow_instance_context = self.loads()
        workflow_instance_context.update(context)
        self.dumps(context=workflow_instance_context)

    def do_transition(
        self, transition, comment=None, extra_data=None, user=None
    ):
        comment = comment or ''
        extra_data = extra_data or {}

        try:
            queryset_transitions = self.get_queryset_valid_transitions(user=user).all()

            if queryset_transitions.filter(pk=transition.pk).exists():
                if extra_data:
                    self.do_context_update(context=extra_data)

                return transition.do_execute(
                    comment=comment, extra_data=json.dumps(obj=extra_data),
                    user=user, workflow_instance=self
                )
        except AttributeError:
            if settings.DEBUG:
                raise

    def dumps(self, context):
        self.context = json.dumps(obj=context)
        self.save()

    def get_context(self):
        self.document.refresh_from_db()
        context = {'workflow_instance': self}
        context['workflow_instance_context'] = self.loads()
        return context

    def get_current_state(self):
        self.refresh_from_db()

        return self.state_active

    def get_last_log_entry(self):
        return self.log_entries.order_by('datetime').last()

    def get_last_log_entry_datetime(self):
        last_log_entry = self.get_last_log_entry()

        if last_log_entry:
            return last_log_entry.datetime
        else:
            return self.datetime

    def get_last_transition(self):
        last_log_entry = self.get_last_log_entry()
        if last_log_entry:
            return last_log_entry.transition

    def get_queryset_valid_transitions(self, user=None):
        current_state = self.get_current_state()

        queryset = current_state.origin_transitions.all()

        if user:
            queryset = AccessControlList.objects.restrict_queryset(
                permission=permission_workflow_instance_transition,
                queryset=queryset, user=user
            )

        condition_context = {'workflow_instance': self}
        for entry in queryset:
            condition_result = entry.evaluate_condition(
                context=condition_context
            )
            if not condition_result:
                queryset = queryset.exclude(id=entry.pk)

        return queryset

    def get_runtime_context(self):
        return self.loads()

    def loads(self):
        return json.loads(s=self.context or '{}')


class WorkflowInstanceLogEntryBusinessLogicMixin:
    def get_destination_state(self):
        if self.transition:
            return self.transition.destination_state
        else:
            return self.workflow_instance.workflow.get_state_initial()

    def get_origin_state(self):
        if self.transition:
            return self.transition.origin_state

    def get_extra_data(self):
        WorkflowTransitionField = apps.get_model(
            app_label='document_states', model_name='WorkflowTransitionField'
        )

        result = {}
        extra_data = self.loads()

        for key, value in extra_data.items():
            try:
                field = self.transition.fields.get(name=key)
            except WorkflowTransitionField.DoesNotExist:
                """
                There is a reference for a field that does not exist or
                has been deleted.
                """
            else:
                result[field.label] = value

        return result

    def loads(self):
        return json.loads(s=self.extra_data or '{}')
