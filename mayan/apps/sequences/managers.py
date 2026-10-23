import logging

from django.db import models, transaction

from .events import (
    event_sequence_exhausted, event_sequence_reset, event_sequence_used
)
from .exceptions import SequenceExhausted, SequenceValueCountInvalid
from .literals import ON_LIMIT_WRAP
from .settings import setting_value_count_maximum

logger = logging.getLogger(name=__name__)


class SequenceManager(models.Manager):
    def do_reset(self, sequence, position=0, user=None):
        with transaction.atomic():
            sequence_locked = self.select_for_update().get(pk=sequence.pk)
            sequence_locked.position = position
            sequence_locked._event_ignore = True
            sequence_locked.save(
                update_fields=('position',)
            )

        sequence.refresh_from_db(
            fields=('position',)
        )

        event_sequence_reset.commit(actor=user, target=sequence)

        return sequence

    def do_value_list_next(self, sequence, count=1, user=None):
        if count < 1:
            raise SequenceValueCountInvalid(
                'The number of requested values must be at least one.'
            )

        value_count_maximum = setting_value_count_maximum.value

        if count > value_count_maximum:
            raise SequenceValueCountInvalid(
                'The number of requested values cannot be greater than '
                '{}.'.format(value_count_maximum)
            )

        try:
            with transaction.atomic():
                sequence_locked = self.select_for_update().get(pk=sequence.pk)

                backend_instance = sequence_locked.get_backend_instance()
                position_limit = backend_instance.get_position_limit()
                position_start = sequence_locked.position

                if position_limit is not None:
                    if count > position_limit:
                        raise SequenceExhausted(
                            'Sequence `{}` can never provide {} values; it '
                            'holds {} positions in total.'.format(
                                sequence_locked.internal_name, count,
                                position_limit
                            )
                        )

                    if position_start + count > position_limit:
                        if sequence_locked.on_limit == ON_LIMIT_WRAP:
                            position_start = 0
                        else:
                            raise SequenceExhausted(
                                'Sequence `{}` is exhausted. Position {} of '
                                '{}.'.format(
                                    sequence_locked.internal_name,
                                    position_start, position_limit
                                )
                            )

                value_list = [
                    backend_instance.get_value(position=position)
                    for position in range(
                        position_start, position_start + count
                    )
                ]

                sequence_locked.position = position_start + count
                sequence_locked._event_ignore = True
                sequence_locked.save(
                    update_fields=('position',)
                )
        except SequenceExhausted:
            event_sequence_exhausted.commit(actor=user, target=sequence)
            raise

        sequence.refresh_from_db(
            fields=('position',)
        )

        event_sequence_used.commit(actor=user, target=sequence)

        return value_list

    def get_for_document_type(self, document_type):
        return self.filter(document_types=document_type)

    def get_for_document_types(self, queryset):
        return self.filter(
            document_types__in=queryset.values('pk')
        ).distinct()
