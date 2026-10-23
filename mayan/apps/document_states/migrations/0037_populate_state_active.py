import logging

from django.db import migrations

logger = logging.getLogger(name=__name__)


def code_populate_state_active(apps, schema_editor):
    WorkflowInstance = apps.get_model(
        app_label='document_states',
        model_name='WorkflowInstance'
    )

    def get_current_state(self):
        last_transition = self.get_last_transition()

        if last_transition:
            return last_transition.destination_state
        else:
            return self.get_workflow_template_initial_state()

    def get_last_log_entry(self):
        return self.log_entries.order_by('datetime').last()

    def get_last_transition(self):
        last_log_entry = self.get_last_log_entry()
        if last_log_entry:
            return last_log_entry.transition

    def get_workflow_template_initial_state(self):
        return self.workflow.states.filter(
            initial=True
        ).order_by('pk').first()

    WorkflowInstance.get_current_state = get_current_state
    WorkflowInstance.get_last_log_entry = get_last_log_entry
    WorkflowInstance.get_last_transition = get_last_transition
    WorkflowInstance.get_workflow_template_initial_state = get_workflow_template_initial_state

    for workflow_instance in WorkflowInstance.objects.all():
        state_active = workflow_instance.get_current_state()

        if state_active:
            workflow_instance.state_active = state_active
            workflow_instance.save()
        else:
            logger.error(
                'Cannot migrate workflow instance. The workflow template '
                '`%s (ID %d)` does not have an initial state. The invalid '
                'workflow instance will be deleted. Relaunch the workflow '
                'for document ID `%d`.',
                str(workflow_instance.workflow.label),
                workflow_instance.workflow.pk, workflow_instance.document_id
            )

            workflow_instance.delete()


class Migration(migrations.Migration):
    dependencies = [
        ('document_states', '0036_workflowinstance_state_active')
    ]

    operations = [
        migrations.RunPython(
            code=code_populate_state_active,
            reverse_code=migrations.RunPython.noop
        )
    ]
