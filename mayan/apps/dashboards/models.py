from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import StoredDashboardManager
from .model_mixins import StoredDashboardBusinessLogicMixin


class StoredDashboard(StoredDashboardBusinessLogicMixin, models.Model):
    _ordering_fields = ('name',)

    name = models.CharField(
        max_length=128, unique=True, verbose_name=_(message='Name')
    )

    objects = StoredDashboardManager()

    class Meta:
        ordering = ('name',)
        verbose_name = _(message='Stored dashboard')
        verbose_name_plural = _(message='Stored dashboards')

    def __str__(self):
        return str(self.label)
