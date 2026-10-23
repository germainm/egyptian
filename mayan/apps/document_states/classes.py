import logging

from django.apps import apps
from django.db.utils import OperationalError, ProgrammingError
from django.utils.translation import gettext_lazy as _

from mayan.apps.backends.classes import DynamicFormModelBackend
from mayan.apps.common.classes import PropertyHelper
from mayan.apps.templating.template_backends import Template

from .exceptions import WorkflowStateActionError

logger = logging.getLogger(name=__name__)


class DocumentStateHelper(PropertyHelper):
    @staticmethod
    @property
    def constructor(*args, **kwargs):
        return DocumentStateHelper(*args, **kwargs)

    def get_result(self, name):
        return self.instance.workflows.get(workflow__internal_name=name)


class WorkflowAction(DynamicFormModelBackend):
    _backend_app_label = 'document_states'
    _backend_model_name = 'WorkflowStateAction'
    _loader_module_name = 'workflow_actions'

    form_fieldsets = (
        (
            _(message='General'), {
                'fields': ('label', 'enabled', 'when', 'condition')
            }
        ),
    )

    @classmethod
    def clean(cls, request, form_data=None, instance=None):
        return form_data

    @classmethod
    def get_choices(cls):
        apps_name_map = {
            app.name: app for app in apps.get_app_configs()
        }

        apps_workflow_action_map = {}

        for klass in WorkflowAction.get_all():
            for app_name, app in apps_name_map.items():
                if klass.__module__.startswith(app_name):
                    apps_workflow_action_map.setdefault(
                        app, []
                    )
                    apps_workflow_action_map[app].append(
                        (
                            klass.backend_id, klass.label
                        )
                    )

        result = [
            (app.verbose_name, workflow_actions) for app, workflow_actions in apps_workflow_action_map.items()
        ]

        return sorted(
            result, key=lambda x: (
                x[0], x[1]
            )
        )

    @classmethod
    def migrate(cls):
        WorkflowStateAction = apps.get_model(
            app_label='document_states', model_name='WorkflowStateAction'
        )
        for previous_dotted_path in cls.previous_dotted_paths:
            try:
                WorkflowStateAction.objects.filter(
                    backend_path=previous_dotted_path
                ).update(
                    backend_path=cls.id()
                )
            except (OperationalError, ProgrammingError):
                return

    def execute(self, context):
        raise NotImplementedError

    @classmethod
    def get_form_schema(cls, workflow_template_state, **kwargs):
        cls.workflow_template_state = workflow_template_state
        return super().get_form_schema(**kwargs)

    def render_field(self, field_name, context):
        try:
            template_string = self.kwargs.get(field_name, '')
            template = Template(template_string=template_string)
            result = template.render(context=context)
        except Exception as exception:
            raise WorkflowStateActionError(
                _(message='%(field_name)s template error: %(exception)s') % {
                    'field_name': field_name, 'exception': exception
                }
            )

        logger.debug('%s template result: %s', field_name, result)

        return result


class WorkflowActionNull(WorkflowAction):
    label = _(message='Null backend')
