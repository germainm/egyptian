from .events import event_sequence_edited


def method_document_type_sequences_add(self, queryset, user):
    for model_instance in queryset:
        self.sequences.add(model_instance)
        event_sequence_edited.commit(
            action_object=self, actor=user, target=model_instance
        )


def method_document_type_sequences_remove(self, queryset, user):
    for model_instance in queryset:
        self.sequences.remove(model_instance)
        event_sequence_edited.commit(
            action_object=self, actor=user, target=model_instance
        )
