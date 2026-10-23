from django.apps import apps
from django.contrib.admin.utils import help_text_for_field, label_for_field
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db.models import Manager
from django.db.models.query import QuerySet


class AutoHelpTextLabelFieldMixin:
    def bind(self, *args, **kwargs):
        result = super().bind(*args, **kwargs)

        try:
            model = self.root.Meta.model
        except AttributeError:
            return result
        else:
            try:
                field = model._meta.get_field(field_name=self.source)
            except FieldDoesNotExist:
                return result
            else:
                field_name = field.name

                if not self.label:
                    self.label = label_for_field(
                        model=model, name=field_name
                    )

                if not self.help_text:
                    self.help_text = help_text_for_field(
                        model=model, name=field_name
                    )

                return result


class FilteredRelatedFieldMixin:
    def __init__(self, **kwargs):
        self.source_model = kwargs.pop('source_model', None)
        self.source_permission = kwargs.pop('source_permission', None)
        self.source_queryset = kwargs.pop('source_queryset', None)
        self.source_queryset_method = kwargs.pop(
            'source_queryset_method', None
        )

        super().__init__(**kwargs)

    def get_queryset(self):
        AccessControlList = apps.get_model(
            app_label='acls', model_name='AccessControlList'
        )

        if self.source_model:
            queryset = self.source_model._meta.default_manager.all()
        elif self.source_queryset is not None:
            queryset = self.source_queryset
            if isinstance(queryset, (QuerySet, Manager)):
                queryset = queryset.all()
        else:
            method_name = self.source_queryset_method or 'get_{}_queryset'.format(
                self.field_name
            )
            try:
                method = getattr(self.parent, method_name)
            except AttributeError:
                raise ImproperlyConfigured(
                    'Need to provide a source_model, a '
                    'source_queryset, a source_queryset_method, or '
                    'a method named "%s".' % method_name
                )
            else:
                queryset = method()

        assert 'request' in self.context, (
            "`%s` requires the request in the serializer"
            " context. Add `context={'request': request}` when "
            "instantiating the serializer." % self.__class__.__name__
        )

        request = self.context['request']

        if self.source_permission:
            return AccessControlList.objects.restrict_queryset(
                permission=self.source_permission, queryset=queryset,
                user=request.user
            )
        else:
            return queryset
