from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

from .literals import EMPTY_LABEL


class FieldMixinFilteredQueryset:
    def get_queryset(self):
        AccessControlList = apps.get_model(
            app_label='acls', model_name='AccessControlList'
        )

        if self.permission and self.user:
            return AccessControlList.objects.restrict_queryset(
                permission=self.permission, queryset=self.source_queryset,
                user=self.user
            )
        else:
            return self.source_queryset

    def reload(self):
        self.queryset = self.get_queryset()

    def set_source_queryset(
        self, permission=None, source_model=None, source_queryset=None
    ):
        self.source_model = source_model
        self.permission = permission
        self.source_queryset = source_queryset

        if self.source_queryset is None:
            if self.source_model:
                self.source_queryset = self.source_model._meta.default_manager.all()
            else:
                raise ImproperlyConfigured(
                    '{} requires a `source_queryset` or a `source_model` to '
                    'be specified as keyword argument.'.format(
                        self.__class__.__name__
                    )
                )


class FormFieldMixinFilteredQueryset(FieldMixinFilteredQueryset):
    def __init__(
        self, permission=None, source_model=None, source_queryset=None,
        *args, **kwargs
    ):
        self.set_source_queryset(
            permission=permission, source_model=source_model,
            source_queryset=source_queryset
        )

        super().__init__(choices=self.get_choices, *args, **kwargs)

    def get_choices(self):
        queryset = self.queryset

        if not queryset._prefetch_related_lookups:
            queryset = queryset.iterator()

        if not self.required:
            yield (None, EMPTY_LABEL)

        for obj in queryset:
            yield (obj.pk, obj)


class ModelFieldMixinFilteredQuerySet(FieldMixinFilteredQueryset):
    def __init__(
        self, permission=None, source_model=None, source_queryset=None,
        *args, **kwargs
    ):
        self.set_source_queryset(
            permission=permission, source_model=source_model,
            source_queryset=source_queryset
        )

        super().__init__(
            queryset=self.source_queryset.none(), *args, **kwargs
        )
