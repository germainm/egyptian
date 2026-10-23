import logging

from django.db import models

from mayan.apps.databases.manager_mixins import ManagerMinixCreateBulk

logger = logging.getLogger(name=__name__)


class FileMetadataEntryManager(ManagerMinixCreateBulk, models.Manager):
    pass


class ModelManagerDocumentTypeDriverConfigurationValid(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()

        return queryset.filter(stored_driver__exists=True)


class ModelManagerStoredDriverValid(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()

        return queryset.filter(exists=True)
