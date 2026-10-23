from django.apps import apps
from django.core.exceptions import AppRegistryNotReady
from django.db.utils import OperationalError, ProgrammingError
from django.utils.encoding import force_str

from mayan.apps.common.serialization import yaml_dump, yaml_load
from ..domains import SettingDomain


class SettingDomainModel(SettingDomain):
    name = 'model'

    @staticmethod
    def deserialize_stream(stream):
        return yaml_load(stream=stream)

    @staticmethod
    def serialize_data(data):
        result = yaml_dump(
            allow_unicode=True, data=data, default_flow_style=False
        )
        if force_str(s=result).endswith('...\n'):
            result = result[:-4]

        return result

    @classmethod
    def do_key_remove(cls, key):
        UpdatedStoredSetting = apps.get_model(
            app_label='smart_settings', model_name='UpdatedStoredSetting'
        )

        queryset = UpdatedStoredSetting.objects.filter(key=key)
        queryset.delete()

    @classmethod
    def do_key_revert(cls, key):
        cls.do_key_remove(key=key)

    @classmethod
    def do_key_update_value_pending(cls, key, value):
        UpdatedStoredSetting = apps.get_model(
            app_label='smart_settings', model_name='UpdatedStoredSetting'
        )

        value_serialized = cls.serialize_data(data=value)

        UpdatedStoredSetting.objects.update_or_create(
            defaults={
                'value': value_serialized,
            }, key=key
        )

    @classmethod
    def do_ready(cls, data):
        UpdatedStoredSetting = apps.get_model(
            app_label='smart_settings', model_name='UpdatedStoredSetting'
        )

        queryset = UpdatedStoredSetting.objects.all()

        try:
            queryset.delete()
        except (OperationalError, ProgrammingError):
            """
            Non fatal. Non initialized installation. Ignore exception.
            """


    @classmethod
    def get_key_value_pending_map(cls):
        try:
            UpdatedStoredSetting = apps.get_model(
                app_label='smart_settings', model_name='UpdatedStoredSetting'
            )
        except AppRegistryNotReady:
            return {}

        try:
            queryset = UpdatedStoredSetting.objects.all()

            return {
                item.key: cls.deserialize_stream(stream=item.value)
                for item in queryset
            }
        except (OperationalError, ProgrammingError):
            """
            Non fatal. Non initialized installation. Ignore exception.
            """
            return {}

    @classmethod
    def get_key_value_pending(cls, key):
        try:
            UpdatedStoredSetting = apps.get_model(
                app_label='smart_settings', model_name='UpdatedStoredSetting'
            )
        except AppRegistryNotReady:
            raise KeyError
        else:
            try:
                updated_setting = UpdatedStoredSetting.objects.get(key=key)
            except UpdatedStoredSetting.DoesNotExist:
                raise KeyError
            except (OperationalError, ProgrammingError):
                """
                Non fatal. Non initialized installation. Ignore exception.
                """
                raise KeyError
            else:
                value = updated_setting.value

                value_deserialized = cls.deserialize_stream(stream=value)

                return value_deserialized
