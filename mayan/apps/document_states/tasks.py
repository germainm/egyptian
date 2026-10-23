import logging

from django.apps import apps
from django.contrib.auth import get_user_model

from mayan.celery import app

logger = logging.getLogger(name=__name__)


@app.task(ignore_result=True)
def task_launch_all_workflows(user_id=None):
    Document = apps.get_model(app_label='documents', model_name='Document')
    Workflow = apps.get_model(
        app_label='document_states', model_name='Workflow'
    )

    User = get_user_model()

    if user_id:
        user = User.objects.get(pk=user_id)
    else:
        user = None

    logger.debug('Start launching workflows')
    for document in Document.valid.all():
        Workflow.objects.launch_for(document=document, user=user)

    logger.debug('Finished launching workflows')


@app.task(ignore_result=True)
def task_launch_workflow(workflow_id, user_id=None):
    Document = apps.get_model(app_label='documents', model_name='Document')
    Workflow = apps.get_model(
        app_label='document_states', model_name='Workflow'
    )

    User = get_user_model()

    if user_id:
        user = User.objects.get(pk=user_id)
    else:
        user = None

    workflow = Workflow.objects.get(pk=workflow_id)

    logger.debug('Start launching workflow: %d', workflow_id)
    queryset_documents = Document.valid.filter(
        document_type__in=workflow.document_types.all()
    )
    for document in queryset_documents:
        workflow.launch_for(document=document, user=user)

    logger.debug('Finished launching workflow: %d', workflow_id)


@app.task(ignore_result=True)
def task_launch_workflow_for(document_id, workflow_id, user_id=None):
    Document = apps.get_model(app_label='documents', model_name='Document')
    Workflow = apps.get_model(
        app_label='document_states', model_name='Workflow'
    )

    User = get_user_model()

    if user_id:
        user = User.objects.get(pk=user_id)
    else:
        user = None

    document = Document.valid.get(pk=document_id)
    workflow = Workflow.objects.get(pk=workflow_id)

    logger.debug(
        'Start launching workflow: %d for document: %d',
        workflow_id, document_id
    )
    workflow.launch_for(document=document, user=user)

    logger.debug(
        'Finished launching workflow: %d for document: %d', workflow_id,
        document_id
    )


@app.task(ignore_result=True)
def task_launch_all_workflow_for(document_id):
    Document = apps.get_model(app_label='documents', model_name='Document')
    Workflow = apps.get_model(
        app_label='document_states', model_name='Workflow'
    )

    document = Document.valid.get(pk=document_id)

    logger.debug(
        'Start launching all workflows for document: %d', document_id
    )
    Workflow.objects.launch_for(document=document)

    logger.debug(
        'Finished launching all workflows for document: %d', document_id
    )


@app.task(ignore_result=True)
def task_workflow_instance_do_check_escalation(workflow_instance_id):
    WorkflowInstance = apps.get_model(
        app_label='document_states', model_name='WorkflowInstance'
    )

    workflow_instance = WorkflowInstance.objects.get(pk=workflow_instance_id)
    workflow_instance.do_check_escalation()


@app.task(ignore_result=True)
def task_workflow_instance_do_check_escalation_all():
    WorkflowInstance = apps.get_model(
        app_label='document_states', model_name='WorkflowInstance'
    )
    WorkflowStateEscalation = apps.get_model(
        app_label='document_states', model_name='WorkflowStateEscalation'
    )

    queryset_workflow_templates = WorkflowStateEscalation.objects.values(
        'state__workflow'
    )

    queryset_workflow_instance = WorkflowInstance.valid.filter(
        workflow__in=queryset_workflow_templates
    )

    for workflow_instance in queryset_workflow_instance:
        task_workflow_instance_do_check_escalation.apply_async(
            kwargs={'workflow_instance_id': workflow_instance.pk}
        )
