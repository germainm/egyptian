from django.utils.translation import gettext_lazy as _

from .events import event_sequence_edited


class SequenceBusinessLogicMixin:
    def do_reset(self, position=0, user=None):
        return self._meta.model.objects.do_reset(
            position=position, sequence=self, user=user
        )

    def do_value_next(self, user=None):
        value_list = self.do_value_list_next(count=1, user=user)

        return value_list[0]

    def do_value_list_next(self, count=1, user=None):
        return self._meta.model.objects.do_value_list_next(
            count=count, sequence=self, user=user
        )

    def document_types_add(self, queryset, user=None):
        for obj in queryset:
            self.document_types.add(obj)
            event_sequence_edited.commit(
                action_object=obj, actor=user, target=self
            )

    def document_types_remove(self, queryset, user=None):
        for obj in queryset:
            self.document_types.remove(obj)
            event_sequence_edited.commit(
                action_object=obj, actor=user, target=self
            )

    def get_position_limit(self):
        backend_instance = self.get_backend_instance()
        return backend_instance.get_position_limit()

    def get_position_remaining(self):
        position_limit = self.get_position_limit()

        if position_limit is None:
            return None

        return max(position_limit - self.position, 0)

    def get_position_remaining_display(self):
        position_remaining = self.get_position_remaining()

        if position_remaining is None:
            return _(message='Unlimited')

        return position_remaining

    get_position_remaining_display.short_description = _(
        message='Positions remaining'
    )

    def get_value_is_unique(self):
        try:
            backend_instance = self.get_backend_instance()
            return backend_instance.get_value_is_unique()
        except Exception:
            return None

    def get_value_is_unique_display(self):
        if self.value_is_unique is None:
            return _(message='Unknown')
        elif self.value_is_unique:
            return _(message='Unique')
        else:
            return _(message='Repeating')

    get_value_is_unique_display.short_description = _(message='Values')
    get_value_is_unique_display.help_text = _(
        message='Whether a value of this sequence identifies a single '
        'position. A sequence whose values repeat cannot serve as an '
        'identifier, though it is a valid generator of a repeating '
        'pattern.'
    )

    def get_value_preview(self):
        try:
            backend_instance = self.get_backend_instance()
            return backend_instance.get_value(
                position=self.position
            )
        except Exception as exception:
            return _(message='Error: %s') % exception

    get_value_preview.short_description = _(message='Next value')
    get_value_preview.help_text = _(
        message='Value that will be returned by the next use of this '
        'sequence. Shown without consuming it.'
    )
