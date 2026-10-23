from django.utils.functional import classproperty

from ..exceptions import (
    SourceActionException, SourceActionExceptionInterface,
    SourceActionExceptionInterfaceUnknown
)
from ..tasks import task_source_backend_action_background_task

from .interfaces import SourceBackendActionInterface
from .mixins.server_upload_mixins import (
    SourceBackendActionMixinServerUpload
)
from .mixins.source_metadata_mixins import (
    SourceBackendActionMixinSourceMetadata
)


class SourceBackendActionMetaclass(type):
    def __new__(mcs, name, bases, attrs):
        new_class = super().__new__(
            mcs, name, bases, attrs
        )

        interface_dict = {}
        for mro_klass in new_class.mro():
            interface_base = getattr(mro_klass, 'Interface', None)
            if interface_base:
                for item_name in dir(interface_base):
                    item = getattr(interface_base, item_name)
                    try:
                        if issubclass(item, SourceBackendActionInterface):
                            interface_dict.setdefault(
                                item_name, []
                            )
                            if item not in interface_dict[item_name]:
                                interface_dict[item_name].append(item)
                    except TypeError:
                        pass

        if interface_dict:
            class InterfaceNamespace:
                pass

            for key, value in interface_dict.items():
                InterfaceClass = type(
                    key, tuple(value), {}
                )

                setattr(InterfaceNamespace, key, InterfaceClass)

            setattr(new_class, 'Interface', InterfaceNamespace)

        return new_class


class SourceBackendActionBase(metaclass=SourceBackendActionMetaclass):
    accept_files = False
    confirmation = True
    name = None
    permission = None

    class Interface:
        pass

    @classproperty
    def interface_visible_list(cls):
        for interface in cls.get_interface_list():
            if not interface.hidden:
                yield interface

    @classmethod
    def get_argument_list(cls, interface_name):
        try:
            action_interface = cls.get_interface_class(
                interface_name=interface_name
            )
        except AttributeError:
            return ()
        else:
            return action_interface.get_arguments()

    @classmethod
    def get_interface_list(cls):
        action_interface_namespace = getattr(cls, 'Interface', None)
        interface_list = []

        if action_interface_namespace:
            for item_name in dir(action_interface_namespace):
                item = getattr(action_interface_namespace, item_name)
                try:
                    if issubclass(item, SourceBackendActionInterface):
                        interface_list.append(item)
                except TypeError:
                    pass

        return interface_list

    def __init__(self, source):
        self.source = source

    def __str__(self):
        return 'Source backend action "{}"'.format(self.name)

    def _background_task(self, **kwargs):
        return {}

    def _execute(self, **kwargs):
        background_task_kwargs = self.get_task_kwargs(**kwargs)

        task_source_backend_action_background_task.apply_async(
            kwargs=background_task_kwargs
        )

    def background_task(self, interface_load_kwargs=None):
        interface_load_kwargs = interface_load_kwargs or {}

        interface_instance = self.get_interface_instance(
            interface_name='Task'
        )

        task_kwargs = interface_instance.load(**interface_load_kwargs)

        self._background_task(**task_kwargs)

    def execute(
        self, interface_name, interface_load_kwargs=None,
        interface_retrieve_kwargs=None
    ):
        interface_load_kwargs = interface_load_kwargs or {}
        interface_retrieve_kwargs = interface_retrieve_kwargs or {}
        interface_instance = self.get_interface_instance(
            interface_name=interface_name
        )

        try:
            execute_kwargs = interface_instance.load(**interface_load_kwargs)
        except SourceActionException as exception:
            raise SourceActionException(
                'Unable to execute action `{}`; {}'.format(
                    self.name, exception
                )
            ) from exception

        backend_instance = self.source.get_backend_instance()

        allow_action_execution = backend_instance.get_allow_action_execute(
            action=self, action_execute_kwargs=execute_kwargs
        )

        if allow_action_execution:
            action_data = self._execute(**execute_kwargs)
        else:
            action_data = None

        return interface_instance.retrieve(
            context=interface_retrieve_kwargs, data=action_data
        )

    def get_confirmation_context(
        self, interface_name, interface_load_kwargs=None
    ):
        interface_load_kwargs = interface_load_kwargs or {}

        interface_instance = self.get_interface_instance(
            interface_name=interface_name
        )

        try:
            result = interface_instance.get_confirmation_context(
                **interface_load_kwargs
            )
        except Exception as exception:
            raise SourceActionExceptionInterface(
                'Unable to get interface confirmation context; {}'.format(
                    exception
                )
            ) from exception

        return result

    def get_document_file_task_kwargs(self, **kwargs):
        return {}

    def get_document_task_kwargs(self, **kwargs):
        return {}

    def get_interface_class(self, interface_name):
        action_interface_namespace = getattr(self, 'Interface')

        try:
            return getattr(action_interface_namespace, interface_name)
        except AttributeError:
            raise SourceActionExceptionInterfaceUnknown(
                'Unknown interface `{}` for action `{}`.'.format(
                    interface_name, self.name
                )
            )

    def get_interface_instance(self, interface_name):
        action_interface_class = self.get_interface_class(
            interface_name=interface_name
        )
        return action_interface_class(action=self)

    def get_task_kwargs(self):
        return {
            'action_name': self.name,
            'action_interface_kwargs': {},
            'source_id': self.source.pk
        }

    def has_interface(self, interface_name):
        return hasattr(self.Interface, interface_name)


class SourceBackendAction(
    SourceBackendActionMixinServerUpload,
    SourceBackendActionMixinSourceMetadata, SourceBackendActionBase
):
    pass


class SourceBackendActionDummy(SourceBackendAction):
    pass
