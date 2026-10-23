import hashlib
import os
import posixpath

from django.core.exceptions import ImproperlyConfigured, SuspiciousFileOperation
from django.core.files.storage import FileSystemStorage
from django.utils._os import safe_join


class ShardedDirectoryFileSystemStorageMixin:
    DEFAULT_SHARDING_LEVELS = 2
    MAXIMUM_SHARDING_LEVELS = 8
    SHARDING_LEVEL_LENGTH = 1

    def __init__(self, *args, sharding_levels=None, **kwargs):
        if sharding_levels is None:
            sharding_levels = self.DEFAULT_SHARDING_LEVELS

        self.sharding_levels = self.get_sharding_levels_validated(
            value=sharding_levels
        )

        super().__init__(*args, **kwargs)

    def get_available_name(self, name, max_length=None):
        if max_length is not None:
            length_overhead = self.get_sharding_overhead_length(name=name)

            max_length = max_length - length_overhead

            if max_length < 1:
                raise SuspiciousFileOperation(
                    'Storage can not find an available filename for "{}". '
                    'The shard directories of this storage need {} '
                    'additional characters. Please make sure that the '
                    'corresponding file field allows sufficient '
                    '"max_length".'.format(name, length_overhead)
                )

        return super().get_available_name(name=name, max_length=max_length)

    def get_resolved_name(self, name):
        sharded_name = self.get_sharded_name(name=name)

        if sharded_name == name:
            return sharded_name

        path_sharded = safe_join(self.location, sharded_name)

        if os.path.lexists(path_sharded):
            return sharded_name

        path_unsharded = safe_join(self.location, name)

        if os.path.lexists(path_unsharded):
            return name

        return sharded_name

    def get_sharded_name(self, name):
        name_normalized = str(name).replace('\\', '/')

        directory_name = posixpath.dirname(name_normalized)
        base_name = posixpath.basename(name_normalized)

        if directory_name or not base_name:
            return name_normalized

        hash_object = hashlib.sha256(
            name_normalized.encode('utf-8')
        )
        digest = hash_object.hexdigest()

        parts = []

        for level in range(self.sharding_levels):
            offset = level * self.SHARDING_LEVEL_LENGTH

            part = digest[offset:offset + self.SHARDING_LEVEL_LENGTH]

            parts.append(part)

        parts.append(name_normalized)

        result = posixpath.join(*parts)

        return result

    def get_sharded_path(self, name):
        sharded_name = self.get_sharded_name(name=name)

        result = safe_join(self.location, sharded_name)

        return result

    def get_sharding_levels_validated(self, value):
        try:
            result = int(value)
        except (TypeError, ValueError):
            raise ImproperlyConfigured(
                'The `sharding_levels` argument of the storage must be an '
                'integer. Received: {}'.format(value)
            )

        if result < 0 or result > self.MAXIMUM_SHARDING_LEVELS:
            raise ImproperlyConfigured(
                'The `sharding_levels` argument of the storage must be a '
                'value from 0 to {}. Received: {}'.format(
                    self.MAXIMUM_SHARDING_LEVELS, result
                )
            )

        return result

    def get_sharding_overhead_length(self, name):
        name_normalized = str(name).replace('\\', '/')

        sharded_name = self.get_sharded_name(name=name)

        result = len(sharded_name) - len(name_normalized)

        return result

    def path(self, name):
        resolved_name = self.get_resolved_name(name=name)

        result = safe_join(self.location, resolved_name)

        return result

    def url(self, name):
        resolved_name = self.get_resolved_name(name=name)

        return super().url(name=resolved_name)


class ShardedDirectoryFileSystemStorage(
    ShardedDirectoryFileSystemStorageMixin, FileSystemStorage
):
    pass
