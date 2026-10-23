from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.events.decorators import method_event
from mayan.apps.events.event_managers import EventManagerSave

from .classes import GPGBackend
from .events import event_key_created
from .literals import KEY_TYPE_CHOICES
from .managers import KeyManager
from .model_mixins import KeyBusinessLogicMixin


class Key(ExtraDataModelMixin, KeyBusinessLogicMixin, models.Model):
    key_data = models.TextField(
        help_text=_(message='ASCII armored version of the key.'),
        verbose_name=_(message='Key data')
    )
    creation_date = models.DateTimeField(
        editable=False, verbose_name=_(message='Creation date')
    )
    expiration_date = models.DateTimeField(
        blank=True, editable=False, null=True,
        verbose_name=_(message='Expiration date')
    )
    fingerprint = models.CharField(
        editable=False, max_length=40, unique=True,
        verbose_name=_(message='Fingerprint')
    )
    length = models.PositiveIntegerField(
        editable=False, verbose_name=_(message='Length')
    )
    algorithm = models.PositiveIntegerField(
        editable=False, verbose_name=_(message='Algorithm')
    )
    user_id = models.TextField(
        editable=False, verbose_name=_(message='User ID')
    )
    key_type = models.CharField(
        choices=KEY_TYPE_CHOICES, editable=False, max_length=3,
        verbose_name=_(message='Type')
    )

    objects = KeyManager()

    class Meta:
        verbose_name = _(message='Key')
        verbose_name_plural = _(message='Keys')

    def __str__(self):
        return '{} - {}'.format(self.key_id, self.user_id)

    def clean(self):
        backend = GPGBackend.get_instance()
        import_results = backend.import_key(key_data=self.key_data)

        if not import_results.key_count:
            raise ValidationError(
                message=_(message='Invalid key data')
            )

        queryset = Key.objects.filter(
            fingerprint=import_results.fingerprints[0]
        )

        if queryset.exists():
            raise ValidationError(
                message=_(message='Key already exists.')
            )

    def get_absolute_url(self):
        return reverse(
            kwargs={'key_id': self.pk}, viewname='django_gpg:key_detail'
        )

    @method_event(
        created={'event': event_key_created, 'target': 'self'},
        event_manager_class=EventManagerSave
    )
    def save(self, *args, **kwargs):
        self.introspect_key_data()
        super().save(*args, **kwargs)
