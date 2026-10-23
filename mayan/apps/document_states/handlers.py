from django.apps import apps

from mayan.apps.document_indexing.tasks import (
    task_index_instance_document_add
)

from .literals import STORAGE_NAME_WORKFLOW_CACHE
from .settings import setting_workflow_image_cache_maximum_size
from .tasks import task_launch_all_workflow_for


def handler_create_workflow_image_cache(sender, **kwargs):
    Cache = apps.get_model(app_label='file_caching', model_name='Cache')
    Cache.objects.update_or_create(
        defaults={
            'maximum_size': setting_workflow_image_cache_maximum_size.value,
        }, defined_storage_name=STORAGE_NAME_WORKFLOW_CACHE,
    )


def handler_launch_workflow_on_create(sender, instance, created, **kwargs):
    if created:
        Workflow = apps.get_model(
            app_label='document_states', model_name='Workflow'
        )

        queryset_workflow_templates = Workflow.objects.get_queryset_auto_launch(
            document_type=instance.document_type
        )

        if queryset_workflow_templates.exists():
            task_launch_all_workflow_for.apply_async(
                kwargs={'document_id': instance.pk}
            )


def handler_launch_workflow_on_type_change(sender, instance, **kwargs):
    Workflow = apps.get_model(
        app_label='document_states', model_name='Workflow'
    )

    queryset_workflow_templates = Workflow.objects.get_queryset_auto_launch(
        document_type=instance.document_type
    )

    if queryset_workflow_templates.exists():
        task_launch_all_workflow_for.apply_async(
            kwargs={'document_id': instance.pk}
        )


def handler_transition_trigger(sender, **kwargs):

    WorkflowTransitionTriggerEvent = apps.get_model(
        app_label='document_states',
        model_name='WorkflowTransitionTriggerEvent'
    )

    action = kwargs['instance']

    WorkflowTransitionTriggerEvent.objects.check_triggers(action=action)




def handler_workflow_template_post_edit(sender, **kwargs):
    if not kwargs.get('created', False):
        for workflow_instance in kwargs['instance'].instances.all():
            task_index_instance_document_add.apply_async(
                kwargs={'document_id': workflow_instance.document.pk}
            )




def handler_workflow_template_state_post_edit(sender, **kwargs):
    if not kwargs.get('created', False):
        for workflow_instance in kwargs['instance'].workflow.instances.all():
            task_index_instance_document_add.apply_async(
                kwargs={'document_id': workflow_instance.document.pk}
            )


def handler_workflow_template_state_pre_delete(sender, **kwargs):
    for workflow_instance in kwargs['instance'].workflow.instances.all():
        workflow_instance.delete()
        task_index_instance_document_add.apply_async(
            kwargs={'document_id': workflow_instance.document.pk}
        )




def handler_workflow_template_transition_post_edit(sender, **kwargs):
    if not kwargs.get('created', False):
        for workflow_instance in kwargs['instance'].workflow.instances.all():
            task_index_instance_document_add.apply_async(
                kwargs={'document_id': workflow_instance.document.pk}
            )


def handler_workflow_template_transition_pre_delete(sender, **kwargs):
    for workflow_instance in kwargs['instance'].workflow.instances.all():
        workflow_instance.delete()
        task_index_instance_document_add.apply_async(
            kwargs={'document_id': workflow_instance.document.pk}
        )
