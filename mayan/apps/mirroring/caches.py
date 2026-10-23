import hashlib

from django.core.cache import caches
from django.utils.encoding import force_bytes

from .settings import (
    setting_document_lookup_cache_timeout, setting_node_lookup_cache_timeout
)


class MirrorFilesystemCache:
    @staticmethod
    def get_key_hash(key):
        key_bytes = force_bytes(s=key)
        return hashlib.sha256(string=key_bytes).hexdigest()

    @staticmethod
    def get_document_key(document):
        key = 'document_pk_{}'.format(document.pk)
        return MirrorFilesystemCache.get_key_hash(key=key)

    @staticmethod
    def get_node_key(node):
        key = 'node_pk_{}'.format(node.pk)
        return MirrorFilesystemCache.get_key_hash(key=key)

    @staticmethod
    def get_path_key(path):
        key = 'path_{}'.format(path)
        return MirrorFilesystemCache.get_key_hash(key=key)

    def __init__(self, name='default'):
        self.cache = caches[name]

    def clear_all(self):
        self.cache.clear()

    def clear_node(self, node):
        node_key = MirrorFilesystemCache.get_node_key(node=node)
        path_cache = self.cache.get(key=node_key)
        if path_cache:
            path = path_cache.get('path')
            if path:
                self.clean_path(path=path)

        self.cache.delete(key=node_key)

    def clear_document(self, document):
        document_key = MirrorFilesystemCache.get_document_key(
            document=document
        )
        path_cache = self.cache.get(key=document_key)
        if path_cache:
            path = path_cache.get('path')
            if path:
                self.clean_path(path=path)

        self.cache.delete(key=document_key)

    def clean_path(self, path):
        key = MirrorFilesystemCache.get_path_key(path=path)
        self.cache.delete(key=key)

    def get_path(self, path):
        key = MirrorFilesystemCache.get_path_key(path=path)
        return self.cache.get(key=key)

    def set_path(self, path, document=None, node=None):
        if document:
            path_key = MirrorFilesystemCache.get_path_key(path=path)
            self.cache.set(
                key=path_key,
                timeout=setting_document_lookup_cache_timeout.value,
                value={'document_pk': document.pk}
            )
            document_key = MirrorFilesystemCache.get_document_key(
                document=document
            )
            self.cache.set(
                key=document_key,
                timeout=setting_document_lookup_cache_timeout.value,
                value={'path': path}
            )
        elif node:
            path_key = MirrorFilesystemCache.get_path_key(path=path)
            self.cache.set(
                key=path_key,
                timeout=setting_node_lookup_cache_timeout.value,
                value={'node_pk': node.pk}
            )
            node_key = MirrorFilesystemCache.get_node_key(node=node)
            self.cache.set(
                key=node_key,
                timeout=setting_node_lookup_cache_timeout.value,
                value={'path': path}
            )
