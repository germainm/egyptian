from mayan.apps.smart_settings.namespace_migrations import (
    SettingNamespaceMigration
)
from mayan.apps.smart_settings.utils import smart_yaml_load


class OCRSettingMigration(SettingNamespaceMigration):
    def ocr_backend_0002(self, value):
        return 'mayan.apps.ocr.backends.tesseract.Tesseract'

    def ocr_backend_arguments_0001(self, value):
        return smart_yaml_load(value=value)
