import hashlib

DEFAULT_BLOCK_SIZE = 65536
DEFAULT_HASH_FUNCTION = hashlib.sha256


def chunk_hash_file_object(
    file_object, block_size=DEFAULT_BLOCK_SIZE, hash_function=None
):
    iterable = iter(
        lambda: file_object.read(block_size), b''
    )

    hash_object = chunk_hash_iterable(
        hash_function=hash_function, iterable=iterable,
    )

    return hash_object


def chunk_hash_iterable(iterable, hash_function=None):
    if hash_function is None:
        hash_function = DEFAULT_HASH_FUNCTION

    hash_object = hash_function()

    for block in iterable:
        hash_object.update(block)

    return hash_object
