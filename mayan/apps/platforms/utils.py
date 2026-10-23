import yaml

from django.utils.html import mark_safe


class Dumper(yaml.Dumper):
    def increase_indent(self, flow=False, *args, **kwargs):
        return super().increase_indent(flow=flow, indentless=False)


def yaml_dump(data, indent):
    result = yaml.dump(
        Dumper=Dumper, data=data, width=1000
    )

    result = result.replace('\'\'\'', '\'')

    output = []

    for line in result.split('\n'):
        if line:
            output.append(
                '{}{}'.format(
                    ' ' * indent, line
                )
            )

    return mark_safe(
        '\n'.join(output)
    )


class EnvironmentFileLoader:
    FILE_NAME_CONFIG_ENV = 'config.env'
    FILE_NAME_CONFIG_LOCALE_ENV = 'config-local.env'

    def __init__(self, filename=FILE_NAME_CONFIG_ENV, skip_local_config=False):
        self.filename = filename
        self.skip_local_config = skip_local_config

    def _do_file_object_content_load(self, file_object):
        result = {}

        for line in file_object:
            key, value = self._do_line_process(line=line)

            if key is not None:
                result[key] = value

        return result

    def _do_line_process(self, line):
        key = None
        value = None

        line_clean = line.strip()

        if line_clean and not line_clean.startswith('#'):
            if '=' in line_clean:
                key, value = line_clean.split('=', 1)

        return key, value

    def do_content_load(self):
        with open(file=self.filename) as file_object:
            config_content = self._do_file_object_content_load(
                file_object=file_object
            )

        if self.filename != EnvironmentFileLoader.FILE_NAME_CONFIG_LOCALE_ENV and not self.skip_local_config:
            try:
                with open(file=EnvironmentFileLoader.FILE_NAME_CONFIG_LOCALE_ENV) as file_object:
                    config_local_content = self._do_file_object_content_load(
                        file_object=file_object
                    )
            except FileNotFoundError:
                """
                Non fatal. Just means this deployment does not overrides the
                default `config.env` file values.
                """
            else:
                config_content.update(config_local_content)

        return config_content


def load_env_file(*args, **kwargs):
    instance = EnvironmentFileLoader(*args, **kwargs)
    result = instance.do_content_load()
    return result


def load_literals():
    import mayan.literals

    result = {}

    for key, value in vars(mayan.literals).items():
        if not key.startswith('_'):
            result[key] = value

    return result
