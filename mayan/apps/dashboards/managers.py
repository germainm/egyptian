from django.db import models

from .classes import Dashboard


class StoredDashboardManager(models.Manager):
    def refresh(self):
        for dashboard in Dashboard.get_all():
            self.get_or_create(name=dashboard.name)
