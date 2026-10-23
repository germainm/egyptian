import yaml

from django.utils.safestring import SafeString

try:
    from yaml import CSafeLoader as SafeLoader, CSafeDumper as SafeDumper
except ImportError:
    from yaml import SafeLoader, SafeDumper


def yaml_dump(**kwargs):
    defaults = {'Dumper': SafeDumper}
    defaults.update(kwargs)

    return yaml.dump(**defaults)


def yaml_load(**kwargs):
    stream = kwargs['stream']

    if isinstance(stream, SafeString):
        stream = stream.strip()
        kwargs['stream'] = stream

    defaults = {'Loader': SafeLoader}
    defaults.update(kwargs)

    return yaml.load(**defaults)
