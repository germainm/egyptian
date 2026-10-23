import re


class SettingNamespaceMigration:
    @staticmethod
    def get_method_name(setting):
        return setting.global_name.lower()

    def __init__(self, namespace):
        self.namespace = namespace

    def get_method_name_full(self, setting, version):
        method_name = self.get_method_name(setting=setting)

        return '{}_{}'.format(method_name, version)

    def get_is_value_explicit(self, global_name):
        cluster = self.namespace.cluster

        try:
            value, domain_dict = cluster.get_domains_value(key=global_name)
        except KeyError:
            return False
        else:
            return value is not None

    def get_value_renamed(
        self, global_name, global_name_old, value, value_fallback
    ):
        if self.get_is_value_explicit(global_name=global_name):
            return value

        cluster = self.namespace.cluster

        try:
            value_old, domain_dict = cluster.get_domains_value(
                key=global_name_old
            )
        except KeyError:
            return value_fallback
        else:
            return value_old

    def do_setting_migrate(self, setting):
        namespace = self.namespace
        cluster = setting.get_cluster()

        namespace_version_previous, namespace_version = cluster.get_namespace_version_list(
            namespace=namespace
        )

        if namespace_version_previous != namespace_version:
            setting_method_name = SettingNamespaceMigration.get_method_name(
                setting=setting
            )

            pattern = r'{}_\d{{4}}'.format(setting_method_name)
            setting_methods = re.findall(
                pattern=pattern, string='\n'.join(
                    dir(self)
                )
            )

            version_list = [
                method.replace(
                    '{}_'.format(setting_method_name), ''
                ) for method in setting_methods
            ]

            try:
                start = version_list.index(namespace_version_previous)
            except ValueError:
                start = 0

            try:
                end = version_list.index(namespace.version)
            except ValueError:
                end = None

            value = setting.value

            for version in version_list[start:end]:
                method = getattr(
                    self, self.get_method_name_full(
                        setting=setting, version=version
                    ), None
                )
                if method:
                    value = method(value=value)

            setting.do_value_override(value=value)
