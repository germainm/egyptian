from django.apps import apps
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from mayan.apps.documents.models.document_models import Document
from mayan.apps.templating.template_backends import Template

from .events import event_smart_link_edited
from .literals import INCLUSION_AND, INCLUSION_OR


class ResolvedSmartLinkBusinessLogicMixin:
    def get_label_for(self, document):
        return self.get_dynamic_label(document=document) or self.label


class SmartLinkBusinessLogicMixin:
    def document_types_add(self, queryset, user):
        for obj in queryset:
            self.document_types.add(obj)
            event_smart_link_edited.commit(
                action_object=obj, actor=user, target=self
            )

    def document_types_remove(self, queryset, user):
        for obj in queryset:
            self.document_types.remove(obj)
            event_smart_link_edited.commit(
                action_object=obj, actor=user, target=self
            )

    def get_dynamic_label(self, document):
        if self.dynamic_label:
            try:
                template = Template(template_string=self.dynamic_label)
                return template.render(
                    context={'document': document}
                )
            except Exception as exception:
                return _(
                    message='Error generating dynamic label; %s'
                ) % exception
        else:
            return None

    def get_linked_documents_for(self, document):
        if document.document_type.pk not in self.document_types.values_list('pk', flat=True):
            raise Exception(
                _(
                    message='This smart link is not allowed for the selected '
                    'document\'s type.'
                )
            )

        smart_link_query = Q()

        for condition in self.conditions.filter(enabled=True):
            template = Template(template_string=condition.expression)

            condition_query = Q(
                **{
                    '{}__{}'.format(
                        condition.foreign_document_data, condition.operator
                    ): template.render(
                        context={'document': document}
                    )
                }
            )
            if condition.negated:
                condition_query = ~condition_query

            if condition.inclusion == INCLUSION_AND:
                smart_link_query &= condition_query
            elif condition.inclusion == INCLUSION_OR:
                smart_link_query |= condition_query

        if smart_link_query:
            queryset = Document.objects.filter(smart_link_query)
        else:
            queryset = Document.objects.none()

        return Document.valid.filter(
            pk__in=queryset.values('pk')
        )

    def resolve_for(self, document):
        ResolvedSmartLink = apps.get_model(
            app_label='linking', model_name='ResolvedSmartLink'
        )

        return ResolvedSmartLink(
            smart_link=self, queryset=self.get_linked_documents_for(
                document=document
            )
        )


class SmartLinkConditionBusinessLogicMixin:
    def get_full_label(self):
        return '{} foreign {} {} {} {}'.format(
            self.get_inclusion_display(),
            self.foreign_document_data, _(message='not') if self.negated else '',
            self.get_operator_display(), self.expression
        )

    get_full_label.short_description = _(message='Full label')
