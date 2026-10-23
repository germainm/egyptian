import logging

from django.apps import apps
from django.core.files import File

from mayan.apps.sources.exceptions import SourceActionExceptionRejected
from mayan.apps.sources.source_backend_actions.interfaces import (
    SourceBackendActionInterface, SourceBackendActionInterfaceRequestRESTAPI,
    SourceBackendActionInterfaceRequestViewForm,
    SourceBackendActionInterfaceTask
)
from mayan.apps.storage.compressed_files import Archive
from mayan.apps.storage.exceptions import ArchiveContentError, NoMIMETypeMatch

from ..source_backends.literals import (
    SOURCE_UNCOMPRESS_API_SLUG_TO_CODE, SOURCE_UNCOMPRESS_CHOICE_ALWAYS,
    SOURCE_UNCOMPRESS_CHOICE_ALWAYS_KEEP_EMPTY,
    SOURCE_UNCOMPRESS_CHOICE_ALWAYS_KEEP_ORIGINAL,
    SOURCE_UNCOMPRESS_CHOICE_ASK, SOURCE_UNCOMPRESS_CHOICE_NEVER,
    SOURCE_UNCOMPRESS_CHOICES_EXPAND
)

from .arguments import (
    argument_expand, argument_expand_mode, argument_uncompress
)

logger = logging.getLogger(name=__name__)


class SourceBackendActionMixinCompressedBase:
    def _background_task(self, uncompress, **kwargs):
        result = super()._background_task(**kwargs)

        if result:

            SharedUploadedFile = apps.get_model(
                app_label='storage', model_name='SharedUploadedFile'
            )

            original_server_upload_entry_list = result.pop(
                'server_upload_entry_list'
            )

            extracted_server_upload_entry_list = []

            expand = uncompress in SOURCE_UNCOMPRESS_CHOICES_EXPAND
            keep_original = uncompress == SOURCE_UNCOMPRESS_CHOICE_ALWAYS_KEEP_ORIGINAL
            keep_if_empty = uncompress == SOURCE_UNCOMPRESS_CHOICE_ALWAYS_KEEP_EMPTY

            if expand:
                for original_server_upload_entry in original_server_upload_entry_list:
                    original_server_upload_entry_extra_data = original_server_upload_entry.copy()
                    original_server_upload_entry_extra_data.pop(
                        'shared_uploaded_file_id'
                    )

                    original_shared_uploaded_file_id = original_server_upload_entry.get(
                        'shared_uploaded_file_id'
                    )

                    original_shared_uploaded_file = SharedUploadedFile.objects.get(
                        pk=original_shared_uploaded_file_id
                    )

                    member_found = False

                    try:
                        with original_shared_uploaded_file.open(mode='rb') as shared_uploaded_file_object:
                            compressed_file = Archive.open(file_object=shared_uploaded_file_object)
                            for compressed_file_member in compressed_file.members():
                                with compressed_file.open_member(filename=compressed_file_member) as compressed_file_member_file_object:
                                    member_found = True
                                    shared_uploaded_file = SharedUploadedFile.objects.create(
                                        file=File(compressed_file_member_file_object)
                                    )
                                    server_upload_entry = original_server_upload_entry_extra_data.copy()
                                    server_upload_entry['shared_uploaded_file_id'] = shared_uploaded_file.pk
                                    extracted_server_upload_entry_list.append(
                                        server_upload_entry
                                    )
                    except NoMIMETypeMatch:
                        if keep_original or keep_if_empty:
                            logger.debug(
                                msg='Not expanding; Exception: NoMIMETypeMatch'
                            )
                            extracted_server_upload_entry_list.append(
                                original_server_upload_entry
                            )
                            continue
                        else:
                            logger.warning(
                                'Received a non-archive file for source id: %s '
                                'configured to always expand its input.',
                                self.source.pk
                            )
                            self.do_server_upload_entry_list_discard(
                                server_upload_entry_list=original_server_upload_entry_list
                            )
                            self.do_server_upload_entry_list_discard(
                                server_upload_entry_list=extracted_server_upload_entry_list
                            )

                            raise SourceActionExceptionRejected(
                                'The uploaded file is not a recognized archive '
                                'type and could not be expanded.'
                            )
                    except ArchiveContentError as exception:
                        logger.warning(
                            'Refusing to expand archive from source id: %s; '
                            '%s: %s', self.source.pk,
                            exception.__class__.__name__, exception
                        )
                        self.do_server_upload_entry_list_discard(
                            server_upload_entry_list=original_server_upload_entry_list
                        )
                        self.do_server_upload_entry_list_discard(
                            server_upload_entry_list=extracted_server_upload_entry_list
                        )

                        raise SourceActionExceptionRejected(
                            '{}; {}'.format(
                                exception.__class__.__name__, exception
                            )
                        ) from exception
                    except Exception as exception:
                        logger.error(
                            'Unexpected error expanding archive from source '
                            'id: %s; %s: %s', self.source.pk,
                            exception.__class__.__name__, exception,
                            exc_info=True
                        )
                        self.do_server_upload_entry_list_discard(
                            server_upload_entry_list=original_server_upload_entry_list
                        )
                        self.do_server_upload_entry_list_discard(
                            server_upload_entry_list=extracted_server_upload_entry_list
                        )

                        raise SourceActionExceptionRejected(
                            '{}; {}'.format(
                                exception.__class__.__name__, exception
                            )
                        ) from exception
                    else:
                        if keep_original:
                            extracted_server_upload_entry_list.append(
                                original_server_upload_entry
                            )
                        elif member_found:
                            self.do_server_upload_entry_list_discard(
                                server_upload_entry_list=(
                                    original_server_upload_entry,
                                )
                            )
                        elif keep_if_empty:
                            logger.debug(
                                'Archive from source id: %s expanded to no '
                                'members; keeping the original file.',
                                self.source.pk
                            )
                            extracted_server_upload_entry_list.append(
                                original_server_upload_entry
                            )
                        else:
                            logger.warning(
                                'Archive from source id: %s expanded to no '
                                'members.', self.source.pk
                            )
                            self.do_server_upload_entry_list_discard(
                                server_upload_entry_list=original_server_upload_entry_list
                            )
                            self.do_server_upload_entry_list_discard(
                                server_upload_entry_list=extracted_server_upload_entry_list
                            )

                            raise SourceActionExceptionRejected(
                                'The uploaded file was expanded but did not '
                                'contain any files to process.'
                            )
            else:
                extracted_server_upload_entry_list = original_server_upload_entry_list

            result['server_upload_entry_list'] = extracted_server_upload_entry_list

            return result

    @staticmethod
    def get_source_backend_uncompress(source_backend):
        method_get_uncompress = getattr(
            source_backend, 'get_uncompress', None
        )

        if method_get_uncompress is None:
            return source_backend.kwargs.get('uncompress')

        return method_get_uncompress()

    def get_task_kwargs(self, uncompress, **kwargs):
        result = super().get_task_kwargs(**kwargs)

        result['action_interface_kwargs'].update(
            {'uncompress': uncompress}
        )

        return result


class SourceBackendActionMixinCompressedInteractive(
    SourceBackendActionMixinCompressedBase
):
    class Interface:
        class Model(SourceBackendActionInterface):
            class Argument:
                expand = argument_expand

            def process_interface_context(self):
                super().process_interface_context()

                source_backend = self.action.source.get_backend_instance()

                if self.context['expand']:
                    code = SOURCE_UNCOMPRESS_CHOICE_ALWAYS
                else:
                    code = SOURCE_UNCOMPRESS_CHOICE_NEVER

                self.action_kwargs['uncompress'] = SourceBackendActionMixinCompressedInteractive.get_resolved_uncompress(
                    code=code, source_backend=source_backend
                )

        class RESTAPI(SourceBackendActionInterfaceRequestRESTAPI):
            class Argument:
                expand = argument_expand
                expand_mode = argument_expand_mode

            def process_interface_context(self):
                super().process_interface_context()

                source_backend = self.action.source.get_backend_instance()

                expand_mode = self.context['expand_mode']
                if expand_mode is not None:
                    code = SourceBackendActionMixinCompressedInteractive.get_uncompress_code_from_slug(slug=expand_mode)
                elif self.context['expand']:
                    code = SOURCE_UNCOMPRESS_CHOICE_ALWAYS
                else:
                    code = SOURCE_UNCOMPRESS_CHOICE_NEVER

                self.action_kwargs['uncompress'] = SourceBackendActionMixinCompressedInteractive.get_resolved_uncompress(
                    code=code, source_backend=source_backend
                )

        class Task(SourceBackendActionInterfaceTask):
            class Argument:
                uncompress = argument_uncompress

            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['uncompress'] = self.context['uncompress']

        class View(SourceBackendActionInterfaceRequestViewForm):
            def process_interface_context(self):
                super().process_interface_context()

                source_backend = self.action.source.get_backend_instance()

                slug = self.context['forms']['source_form'].cleaned_data.get(
                    'expand_mode'
                )
                if slug:
                    code = SourceBackendActionMixinCompressedInteractive.get_uncompress_code_from_slug(slug=slug)
                else:
                    code = SOURCE_UNCOMPRESS_CHOICE_NEVER

                self.action_kwargs['uncompress'] = SourceBackendActionMixinCompressedInteractive.get_resolved_uncompress(
                    code=code, source_backend=source_backend
                )

    @staticmethod
    def get_resolved_uncompress(source_backend, code):
        uncompress = SourceBackendActionMixinCompressedBase.get_source_backend_uncompress(
            source_backend=source_backend
        )

        if uncompress == SOURCE_UNCOMPRESS_CHOICE_ASK:
            return code
        else:
            return uncompress

    @staticmethod
    def get_uncompress_code_from_slug(slug):
        try:
            return SOURCE_UNCOMPRESS_API_SLUG_TO_CODE[slug]
        except KeyError:
            raise SourceActionExceptionRejected(
                'Invalid `expand_mode` value: {!r}. Valid values are: '
                '{}.'.format(
                    slug, ', '.join(SOURCE_UNCOMPRESS_API_SLUG_TO_CODE)
                )
            )


class SourceBackendActionMixinCompressedInteractiveNot(
    SourceBackendActionMixinCompressedBase
):
    class Interface:
        class Model(SourceBackendActionInterface):
            def process_interface_context(self):
                super().process_interface_context()

                source_backend = self.action.source.get_backend_instance()

                self.action_kwargs['uncompress'] = SourceBackendActionMixinCompressedBase.get_source_backend_uncompress(
                    source_backend=source_backend
                )

        class Task(SourceBackendActionInterfaceTask):
            class Argument:
                uncompress = argument_uncompress

            def process_interface_context(self):
                super().process_interface_context()

                self.action_kwargs['uncompress'] = self.context['uncompress']
