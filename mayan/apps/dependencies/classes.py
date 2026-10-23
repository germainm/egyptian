from io import BytesIO
from importlib.metadata import PackageNotFoundError, version
import json
import logging
from pathlib import Path
import shutil
import sys

from furl import furl
from packaging.requirements import Requirement
from packaging.version import Version
import requests
from nodesemver import max_satisfying

from django.apps import apps
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from django.utils.termcolors import colorize
from django.utils.translation import gettext, gettext_lazy as _

from mayan.apps.common.class_mixins import AppsModuleLoaderMixin
from mayan.apps.common.exceptions import ResolverPipelineError
from mayan.apps.common.utils import ResolverPipelineObjectAttribute
from mayan.apps.locales.translatable import join_translatable
from mayan.apps.storage.compressed_files import TarArchive
from mayan.apps.storage.exceptions import CompressionFileError
from mayan.apps.storage.utils import (
    TemporaryDirectory, fs_cleanup, mkdtemp,
    patch_files as storage_patch_files
)

from .algorithms import HashAlgorithm
from .exceptions import DependenciesException
from .literals import DEFAULT_HTTP_TIMEOUT, REGULAR_EXPRESSION_CSS_URL
from .settings import setting_google_fonts_url, setting_npm_registry_url

logger = logging.getLogger(name=__name__)


class Provider:
    pass


class PyPIRespository(Provider):
    url = 'https://pypi.org/'


class GoogleFontsProvider(Provider):
    @property
    def url(self):
        return setting_google_fonts_url.value


class NPMRegistryRespository(Provider):
    @property
    def url(self):
        return setting_npm_registry_url.value


class OperatingSystemProvider(Provider):
    pass


class DependencyGroup:
    _registry = {}

    @classmethod
    def get(cls, name):
        return cls._registry[name]

    @classmethod
    def get_all(cls):
        return sorted(
            cls._registry.values(), key=lambda x: x.label
        )

    def __init__(
        self, attribute_name, label, name, allow_multiple=False,
        help_text=None
    ):
        self.allow_multiple = allow_multiple
        self.attribute_name = attribute_name
        self.label = label
        self.help_text = help_text
        self.name = name

        self.__class__._registry[name] = self

    def __str__(self):
        return str(self.label)

    @staticmethod
    def get_options_for_dependency_group(dependency_group):
        result = []

        for dependency in Dependency.get_all():
            value = ResolverPipelineObjectAttribute.resolve(
                attribute=dependency_group.attribute_name, obj=dependency
            )

            try:
                label = ResolverPipelineObjectAttribute.resolve(
                    attribute='{}_verbose_name'.format(
                        dependency_group.attribute_name
                    ), obj=dependency
                )
            except ResolverPipelineError:
                label = value

            try:
                help_text = ResolverPipelineObjectAttribute.resolve(
                    attribute='{}_help_text'.format(
                        dependency_group.attribute_name
                    ), obj=dependency
                )
            except ResolverPipelineError:
                if dependency_group.allow_multiple:
                    help_text = (None,) * len(value)
                else:
                    help_text = None

            if dependency_group.allow_multiple:
                for entry_index, entry in enumerate(value):
                    dictionary = {
                        'label': label[entry_index],
                        'help_text': help_text[entry_index], 'value': entry
                    }
                    if dictionary not in result:
                        result.append(dictionary)
            else:
                dictionary = {
                    'label': label, 'help_text': help_text, 'value': value
                }
                if dictionary not in result:
                    result.append(dictionary)

        return result

    def get_entries(self):
        options = DependencyGroup.get_options_for_dependency_group(
            dependency_group=self
        )
        result = []

        for option in options:
            result.append(
                DependencyGroupEntry(
                    dependency_group=self, help_text=option['help_text'],
                    label=option['label'], name=option['value']
                )
            )

        return sorted(result, key=lambda x: x.label)

    def get_entry(self, entry_name):
        for entry in self.get_entries():
            if entry.name == entry_name:
                return entry

        raise KeyError('Entry not found.')


class DependencyGroupEntry:
    def __init__(
        self, dependency_group, label, name, help_text=None
    ):
        self.dependency_group = dependency_group
        self.help_text = help_text or ''
        self.label = label
        self.name = name

    def __str__(self):
        return str(self.label)

    def get_dependencies(self):
        dependencies = Dependency.get_for_attribute(
            attribute_name=self.dependency_group.attribute_name,
            attribute_value=self.name
        )

        return Dependency.return_sorted(dependencies=dependencies)


class Dependency(AppsModuleLoaderMixin):
    _loader_module_name = 'dependencies'
    _registry = {}

    @staticmethod
    def return_sorted(dependencies):
        return sorted(
            dependencies, key=lambda x: x.get_label()
        )

    @classmethod
    def _check_all(cls):
        result = []

        for dependency in cls.get_all():
            check = dependency.check()

            if check and any(map(lambda x: x.mark_missing, dependency.environments)):
                check_text = '* {} *'.format(check)
                check_color = check if check else colorize(
                    text=check_text, fg='red', opts=(
                        'bold', 'blink', 'reverse'
                    )
                )

                result.append(
                    {
                        'check': check,
                        'check_color': check_color,
                        'check_text': check_text,
                        'dependency': dependency
                    }
                )

        return result

    @classmethod
    def check_all(cls, as_csv=False, use_color=False):
        if as_csv:
            template = '{},{},{},{},{},{},{}'

            print(
                template.format(
                    gettext(message='Name'), gettext(message='Type'),
                    gettext(message='Version'), gettext(message='App'),
                    gettext(message='Environments'),
                    gettext(message='Other data'), gettext(message='Check')
                )
            )
            for result in cls._check_all():
                dependency = result['dependency']

                print(
                    template.format(
                        dependency.name,
                        str(dependency.class_name_verbose_name),
                        str(
                            dependency.get_version_string()
                        ),
                        str(
                            dependency.app_label_verbose_name()
                        ),
                        str(
                            dependency.get_environments_verbose_name()
                        ),
                        str(
                            dependency.get_other_data()
                        ),
                        str(
                            result['check']
                        )
                    )
                )
        else:
            for result in cls._check_all():
                dependency = result['dependency']
                print('-' * 40)
                print(
                    '* {}'.format(dependency.name)
                )
                print(
                    'Class: {class_name} | Version: {version} '
                    '| App: {app_label} | Environments: {environments} '
                    '| Other data: {other} | Check: {check}'.format(
                        class_name=dependency.class_name_verbose_name,
                        version=dependency.get_version_string(),
                        app_label=dependency.app_label_verbose_name(),
                        environments=dependency.get_environments_verbose_name(),
                        other=dependency.get_other_data(),
                        check=result['check_color'] if use_color else result['check_text']
                    )
                )

        sys.stdout.flush()

    @classmethod
    def get(cls, pk):
        return cls._registry[pk]

    @classmethod
    def get_all(cls, subclass_only=False):
        dependencies = cls._registry.values()
        if subclass_only:
            dependencies = [
                dependency for dependency in dependencies if isinstance(
                    dependency, cls
                )
            ]

        return Dependency.return_sorted(dependencies=dependencies)

    @classmethod
    def get_for_attribute(cls, attribute_name, attribute_value, **kwargs):
        result = []

        for dependency in cls.get_all(**kwargs):
            resolved_attibute_value = ResolverPipelineObjectAttribute.resolve(
                attribute=attribute_name, obj=dependency
            )

            if attribute_value == resolved_attibute_value or attribute_value in resolved_attibute_value:
                result.append(dependency)

        return result

    @classmethod
    def install_multiple(
        cls, app_label=None, force=False, subclass_only=False
    ):
        for dependency in cls.get_all(subclass_only=subclass_only):
            if app_label:
                if app_label == dependency.app_label:
                    dependency.install(force=force)
            else:
                dependency.install(force=force)

    @classmethod
    def uninstall_multiple(cls, app_label=None, subclass_only=False):
        for dependency in cls.get_all(subclass_only=subclass_only):
            if app_label:
                if app_label == dependency.app_label:
                    dependency.uninstall()
            else:
                dependency.uninstall()

    def __init__(
        self, name, environments, app_label=None, help_text=None, label=None,
        legal_text=None, module=None, replace_list=None, version_string=None
    ):
        self._app_label = app_label
        self.environments = environments
        self.help_text = help_text
        self.label = label
        self.legal_text = legal_text
        self.module = module
        self.name = name
        self.package_metadata = None
        self.replace_list = replace_list
        self.repository = self.provider_class()
        self.version_string = version_string

        if not app_label:
            if not module:
                raise DependenciesException(
                    _(message='Need to specify at least one: app_label or module.')
                )

        if self.get_pk() in self.__class__._registry:
            raise DependenciesException(
                _(message='Dependency "%s" already registered.') % self.name
            )

        self.__class__._registry[
            self.get_pk()
        ] = self

    @cached_property
    def app_label(self):
        if not self._app_label:
            app = apps.get_containing_app_config(object_name=self.module)
            return app.label
        else:
            return self._app_label

    def app_label_verbose_name(self):
        return apps.get_app_config(app_label=self.app_label).verbose_name

    def download(self):
        raise NotImplementedError

    def get_copyright_text(self):
        return ''

    def get_legal_text(self):
        if self.legal_text:
            return self.legal_text
        else:
            text_legal_list = []

            text_copyright = self.get_copyright_text()

            if text_copyright:
                text_legal_list.append(text_copyright)
                text_legal_list.append('')

            text_license = self.get_license_text()

            if text_license:
                text_legal_list.append(text_license)

            return '\n'.join(text_legal_list)

    def get_license_text(self):
        return ''

    def install(self, force=False):
        label_full = self.get_label_full()
        print(
            _(message='Installing package: %s... ') % label_full, end=''
        )
        sys.stdout.flush()

        if not force:
            if self.check():
                print(
                    _(message='Already installed.')
                )
            else:
                self._install()
                print(
                    _(message='Complete.')
                )
                sys.stdout.flush()
        else:
            if self.replace_list:
                self.patch_files()
                print(
                    _(message='Complete.')
                )
                sys.stdout.flush()

            self.patch_files()
            print(
                _(message='Complete.')
            )
            sys.stdout.flush()

    def uninstall(self):
        label_full = self.get_label_full()
        print(
            _(message='Uninstalling package: %s... ') % label_full, end=''
        )
        sys.stdout.flush()
        self._uninstall()
        print(
            _(message='Complete.')
        )
        sys.stdout.flush()

    def _install(self):
        raise NotImplementedError

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.name)

    def check(self):
        if self._check():
            return True
        else:
            return False

    def check_string(self):
        if self._check():
            return 'True'
        else:
            return 'False'

    def check_string_verbose_name(self):
        if self._check():
            return _(message='Installed and correct version')
        else:
            return _(message='Missing or incorrect version')

    def _check(self):
        raise NotImplementedError

    def get_help_text(self):
        return self.help_text or ''

    def get_environments(self):
        return [
            environment.name for environment in self.environments
        ]

    def get_environments_help_text(self):
        return [
            environment.help_text for environment in self.environments
        ]

    def get_environments_verbose_name(self):
        environment_label_list = [
            environment.label for environment in self.environments
        ]

        return join_translatable(items=environment_label_list, separator=', ')

    def get_label(self):
        return self.label or self.name

    def get_label_full(self):
        if self.version_string:
            version_string = '({})'.format(self.version_string)
        else:
            version_string = ''

        return '{} {}'.format(
            self.get_label(), version_string
        )

    def get_other_data(self):
        return _(message='None')

    def get_pk(self):
        return self.name

    def get_url(self):
        raise NotImplementedError

    def get_version_string(self):
        return self.version_string or _(message='Not specified')

    def patch_files(self, path=None, replace_list=None):
        print(_(message='Patching files... '), end='')

        try:
            sys.stdout.flush()
        except AttributeError:
            pass

        if not path:
            path = self.get_install_path()

        if not replace_list:
            replace_list = self.replace_list

        storage_patch_files(path=path, replace_list=replace_list)

    def verify(self):
        raise NotImplementedError




class BinaryDependency(Dependency):
    class_name = 'binary'
    class_name_help_text = _(
        message='Executables that are called directly by the code.'
    )
    class_name_verbose_name = _(message='Binary')
    provider_class = OperatingSystemProvider

    def __init__(self, *args, **kwargs):
        self.path = kwargs.pop('path')
        super().__init__(*args, **kwargs)

    def _check(self):
        path = Path(self.path)
        return path.exists()

    def get_other_data(self):
        return 'Path: {}'.format(self.path)


class JavaScriptDependency(Dependency):
    class_name = 'javascript'
    class_name_help_text = _(
        message='JavaScript libraries downloaded the from NPM registry and '
        'used for front-end functionality.'
    )
    class_name_verbose_name = _(message='JavaScript')
    provider_class = NPMRegistryRespository

    def __init__(self, *args, **kwargs):
        self.static_folder = kwargs.pop('static_folder', None)
        return super().__init__(*args, **kwargs)

    def _check(self):
        try:
            package_info = self._read_package_file()
        except FileNotFoundError:
            return False

        versions = [
            package_info['version']
        ]
        version_string = self.version_string

        return max_satisfying(
            loose=True, range_=version_string, versions=versions
        )

    def _read_package_file(self):
        path_install_path = self.get_install_path()
        path_package = path_install_path / 'package.json'

        with path_package.open(mode='rb') as file_object:
            return json.load(file_object)

    def _install(self, include_dependencies=False):
        self.get_metadata()
        print(
            _(message='Downloading... '), end=''
        )
        sys.stdout.flush()
        self.download()
        print(
            _(message='Verifying... '), end=''
        )
        sys.stdout.flush()
        self.verify()
        print(
            _(message='Extracting... '), end=''
        )
        sys.stdout.flush()
        self.extract()

        if include_dependencies:
            dependency_dict = self.version_metadata.get('dependencies', {})
            for name, version_string in dependency_dict.items():
                dependency = JavaScriptDependency(
                    name=name, version_string=version_string
                )
                dependency.install(include_dependencies=False)

    def _uninstall(self, include_dependencies=False):
        print(
            _(message='Uninstalling... '), end=''
        )
        sys.stdout.flush()
        self.delete()

        if include_dependencies:
            dependency_dict = self.version_metadata.get('dependencies', {})
            for name, version_string in dependency_dict.items():
                dependency = JavaScriptDependency(
                    name=name, version_string=version_string
                )
                dependency.uninstall(include_dependencies=False)

    def delete(self):
        path_install = self.get_install_path()
        fs_cleanup(filename=path_install)

    def extract(self, replace_list=None):
        try:
            self._extract(replace_list=replace_list)
        except CompressionFileError as exception:
            raise DependenciesException(
                'The package archive for "{label}" was rejected by an '
                'archive safety limit: {exception} The package is not '
                'necessarily malicious, the limits are conservative by '
                'default.'.format(
                    exception=exception, label=self.get_label_full()
                )
            ) from exception

    def _extract(self, replace_list=None):
        with TemporaryDirectory() as temporary_directory:
            path_compressed_file = self.get_tar_file_path()
            path_temporary = Path(temporary_directory)

            with path_compressed_file.open(mode='rb') as file_object:
                archive = TarArchive.open(file_object=file_object)

                for member in archive.members():
                    member_path = (path_temporary / member).resolve()

                    try:
                        member_path.parent.relative_to(path_temporary)
                    except ValueError:
                        raise DependenciesException(
                            'Suspicious path traversal: {}. Dependency '
                            'might be compromised'.format(member)
                        )
                    else:
                        member_filename = str(member)
                        with archive.open_member(filename=member_filename) as member_archive_file_object:
                            member_path.parent.mkdir(exist_ok=True, parents=True)
                            with member_path.open(mode='wb+') as member_storage_file_object:
                                shutil.copyfileobj(
                                    fsrc=member_archive_file_object,
                                    fdst=member_storage_file_object
                                )

            self.patch_files(
                path=temporary_directory, replace_list=replace_list
            )

            path_install = self.get_install_path()

            shutil.rmtree(
                path=str(path_install), ignore_errors=True
            )

            path_install.mkdir(parents=True)

            path_uncompressed_package = Path(temporary_directory, 'package')
            shutil.rmtree(
                path=str(path_install)
            )
            shutil.copytree(
                src=str(path_uncompressed_package),
                dst=str(path_install)
            )

            shutil.rmtree(path=self.path_cache, ignore_errors=True)

    def download(self):
        self.path_cache = mkdtemp()

        url_tarball = self.version_metadata['dist']['tarball']

        with requests.get(stream=True, timeout=DEFAULT_HTTP_TIMEOUT, url=url_tarball) as response:
            response.raise_for_status()
            with self.get_tar_file_path().open(mode='wb') as file_object:
                shutil.copyfileobj(
                    fsrc=BytesIO(
                        initial_bytes=response.content
                    ), fdst=file_object
                )

    def get_best_version(self):
        versions = self.versions
        version_string = self.version_string

        return max_satisfying(
            versions=versions, range_=version_string, loose=True
        )

    def get_copyright_text(self):
        package_info = self._read_package_file()

        author = package_info.get(
            'author', {}
        )

        try:
            author = author.get('name')
        except AttributeError:
            """It is a single top level entry."""

        author = author or ''

        if author:
            author = 'Copyright: {}'.format(author)

        return author

    def get_license_text(self):
        path_install_path = self.get_install_path()

        for entry in path_install_path.glob(pattern='LICENSE*'):
            with entry.open(mode='r') as file_object:
                return file_object.read()

        try:
            package_info = self._read_package_file()
        except FileNotFoundError:
            return ''
        else:
            return package_info.get('license') or package_info.get(
                'licenses'
            )[0]['type']

    def get_help_text(self):
        description = None

        try:
            description = self._read_package_file().get('description')
        except FileNotFoundError:
            return super().get_help_text()
        else:
            return description

    def get_install_path(self):
        app = apps.get_app_config(app_label=self.app_label)
        result = Path(
            app.path, 'static', self.static_folder or app.label,
            'node_modules', self.name
        )
        return result

    def get_metadata(self):
        url = self.get_url()
        response = requests.get(timeout=DEFAULT_HTTP_TIMEOUT, url=url)
        response.raise_for_status()
        self.package_metadata = response.json()
        self.versions = self.package_metadata['versions'].keys()
        self.version_best = self.get_best_version()
        try:
            self.version_metadata = self.package_metadata['versions'][
                self.version_best
            ]
        except KeyError:
            raise DependenciesException(
                'Best version for dependency %s is not found in '
                'upstream repository.', self.version_best
            )

    def get_tar_file_path(self):
        return Path(
            self.path_cache, self.get_tar_filename()
        )

    def get_tar_filename(self):
        return furl(
            self.version_metadata['dist']['tarball']
        ).path.segments[-1]

    def get_url(self):
        url = furl(self.repository.url)
        url.path.segments += [self.name]
        return url.tostr()

    def verify(self):
        path_tar_file = self.get_tar_file_path()

        try:
            integrity = self.version_metadata['dist']['integrity']
        except KeyError:
            algorithm_name = 'sha1'
            integrity_value = self.version_metadata['dist']['shasum']
        else:
            algorithm_name, integrity_value = integrity.split('-', 1)

        try:
            algorithm_class = HashAlgorithm.get(name=algorithm_name)
        except KeyError:
            raise DependenciesException(
                'Unknown hash algorithm: %s', algorithm_name
            )

        with path_tar_file.open(mode='rb') as file_object:
            algorithm_object = algorithm_class(file_object=file_object)
            algorithm_object.calculate()

        if algorithm_object.get_digest() != integrity_value:
            path_tar_file.unlink()
            raise DependenciesException(
                'Hash of downloaded dependency package "%s" doesn\'t match '
                'online version.', self.get_label_full()
            )


class PythonVersion:
    def __init__(self, string):
        self.version = Version(version=string)

    def __lt__(self, other):
        return self.version < other.version


class PythonDependency(Dependency):
    class_name = 'python'
    class_name_help_text = _(
        message='Python packages downloaded from PyPI.'
    )
    class_name_verbose_name = _(message='Python')
    provider_class = PyPIRespository

    def __init__(self, *args, **kwargs):
        self.attribute_copyright = kwargs.pop(
            'attribute_copyright', '__copyright__'
        )
        self.attribute_license = kwargs.pop(
            'attribute_license', '__license__'
        )
        super().__init__(*args, **kwargs)

    def _check(self):
        requirement_string = '{}{}'.format(self.name, self.version_string)

        try:
            requirement = Requirement(requirement_string=requirement_string)
        except PackageNotFoundError:
            return False
        except Exception as exception:
            raise DependenciesException(
                'Error processing dependency `{}`; {}'.format(
                    requirement_string, exception
                )
            ) from exception
        else:
            try:
                distribution_version_string = version(
                    distribution_name=requirement.name
                )
                distribution_version = Version(
                    version=distribution_version_string
                )
            except PackageNotFoundError:
                return False
            else:
                return distribution_version in requirement.specifier

    def get_copyright_text(self):
        try:
            return import_string(dotted_path=self.attribute_copyright)
        except ImportError:
            return ''

    def get_latest_version(self):
        url = 'https://pypi.python.org/pypi/{}/json'.format(self.name)
        response = requests.get(timeout=DEFAULT_HTTP_TIMEOUT, url=url)
        response.raise_for_status()
        versions = list(
            response.json()['releases']
        )
        versions.sort(key=PythonVersion)
        return versions[-1]

    def get_license_text(self):
        try:
            return import_string(dotted_path=self.attribute_license)
        except ImportError:
            return ''

    def is_latest_version(self):
        return self.version_string == '=={}'.format(
            self.get_latest_version()
        )


class GoogleFontDependency(Dependency):
    class_name = 'google_font'
    class_name_help_text = _(
        message='Fonts downloaded from fonts.googleapis.com.'
    )
    class_name_verbose_name = _(message='Google font')
    provider_class = GoogleFontsProvider
    user_agents = {
        'woff2': 'Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0',
        'woff': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36',
        'ttf': 'Mozilla/5.0 (Linux; U; Android 2.2; en-us; DROID2 GLOBAL Build/S273) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1'
    }

    def __init__(self, *args, **kwargs):
        self.url = kwargs.pop('url')
        self.static_folder = kwargs.pop('static_folder', None)
        super().__init__(*args, **kwargs)

    def _check(self):
        path = self.get_install_path()
        return path.exists()

    def _install(self):
        print(
            _(message='Downloading... '), end=''
        )
        sys.stdout.flush()
        self.download()
        print(
            _(message='Extracting... '), end=''
        )
        sys.stdout.flush()
        self.extract()

    def _uninstall(self):
        print(
            _(message='Uninstalling... '), end=''
        )
        sys.stdout.flush()
        self.delete()

    def delete(self):
        path_install = self.get_install_path()
        fs_cleanup(filename=path_install)

    def download(self):
        self.path_cache = Path(
            mkdtemp()
        )
        self.path_import_file = self.path_cache / 'import.css'

        self.font_files = {}

        url = self.get_url()

        with self.path_import_file.open(mode='w') as file_object:
            for agent_name, agent_string in self.user_agents.items():
                headers = {'User-Agent': agent_string}

                response = requests.get(
                    headers=headers, timeout=DEFAULT_HTTP_TIMEOUT, url=url
                )
                response.raise_for_status()

                stylesheet = response.text

                for line in stylesheet.split('\n'):
                    line_localized = self.get_line_localized(line=line)
                    file_object.write(line_localized)

    def extract(self, replace_list=None):
        path_install = self.get_install_path()

        shutil.rmtree(
            path=str(path_install), ignore_errors=True
        )

        shutil.copytree(
            src=str(self.path_cache), dst=str(path_install)
        )
        shutil.rmtree(
            path=str(self.path_cache), ignore_errors=True
        )

    def get_filename_unique(self, filename):
        filename_list = self.font_files.values()

        if filename not in filename_list:
            return filename

        path_filename = Path(filename)
        filename_stem = path_filename.stem
        filename_suffix = path_filename.suffix

        counter = 1

        while True:
            filename_result = '{}_{}{}'.format(
                filename_stem, counter, filename_suffix
            )

            if filename_result not in filename_list:
                return filename_result

            counter = counter + 1

    def get_font_file_download(self, url):
        filename_cached = self.font_files.get(url)

        if filename_cached:
            return filename_cached

        url_parsed = furl(url)
        filename_remote = url_parsed.path.segments[-1]
        filename = self.get_filename_unique(filename=filename_remote)

        path_font_file = self.path_cache / filename

        with requests.get(stream=True, timeout=DEFAULT_HTTP_TIMEOUT, url=url) as response:
            response.raise_for_status()

            with path_font_file.open(mode='wb') as file_object:
                shutil.copyfileobj(
                    fsrc=BytesIO(
                        initial_bytes=response.content
                    ), fdst=file_object
                )

        self.font_files[url] = filename

        return filename

    def get_install_path(self):
        app = apps.get_app_config(app_label=self.app_label)
        result = Path(
            app.path, 'static', self.static_folder or app.label,
            'google_fonts', self.name
        )
        return result

    def get_line_localized(self, line):
        url_list = REGULAR_EXPRESSION_CSS_URL.findall(string=line)

        result = line

        for url_raw in url_list:
            url = url_raw.strip('\'"')

            if not url:
                continue

            filename = self.get_font_file_download(url=url)
            result = result.replace(url, filename)

        return result

    def get_url(self):
        url_declared = furl(self.url)
        origin = url_declared.origin

        if not self.url.startswith(origin):
            return self.url

        url_provider = self.repository.url
        url_base = url_provider.rstrip('/')

        remainder = self.url[len(origin):]

        return '{}{}'.format(url_base, remainder)


DependencyGroup(
    attribute_name='app_label', label=_(message='Declared in app'), help_text=_(
        message='Show dependencies by the app that declared them.'
    ), name='app'
)
DependencyGroup(
    attribute_name='class_name', label=_(message='Class'), help_text=_(
        message='Show the different classes of dependencies. Classes are '
        'usually divided by language or the file types of the dependency.'
    ), name='class'
)
DependencyGroup(
    attribute_name='check_string', label=_(message='State'), help_text=_(
        message='Show the different states of the dependencies. True means '
        'that the dependencies is installed and is of a correct version. '
        'False means the dependencies is missing or an incorrect version is '
        'present.'
    ), name='state'
)
DependencyGroup(
    allow_multiple=True, attribute_name='get_environments',
    label=_(message='Environments'), help_text=_(
        message='Dependencies required for an environment might not be '
        'required for another. Example environments: Production, '
        'Development.'
    ), name='environment'
)
