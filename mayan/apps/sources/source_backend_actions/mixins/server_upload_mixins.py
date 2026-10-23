from mayan.apps.storage.tasks import task_shared_upload_delete


class SourceBackendActionMixinServerUpload:
    def do_server_upload_entry_list_discard(self, server_upload_entry_list):
        for server_upload_entry in server_upload_entry_list:
            task_shared_upload_delete.apply_async(
                kwargs={
                    'shared_uploaded_file_id': server_upload_entry[
                        'shared_uploaded_file_id'
                    ]
                }
            )
