class CompressionFileError(Exception):
    pass


class ArchiveContentError(CompressionFileError):
    pass


class ArchiveCompressionRatioExceeded(ArchiveContentError):
    pass


class ArchiveInputSizeExceeded(ArchiveContentError):
    pass


class ArchiveMemberSizeExceeded(ArchiveContentError):
    pass


class ArchiveCompressionRatioExceeded(CompressionFileError):
    """
    A member's uncompressed-to-compressed size ratio exceeds the
    configured maximum, characteristic of a zip-bomb / tar-bomb
    payload.
    """


class ArchiveInputSizeExceeded(CompressionFileError):
    """
    The input archive file size exceeds the configured maximum.
    Raised before any parsing is attempted, to prevent the upstream
    library from loading a hostile payload into memory.
    """


class ArchiveMemberSizeExceeded(CompressionFileError):
    """
    A member of the archive has a declared (uncompressed) size that
    exceeds the configured maximum.
    """


class NoMIMETypeMatch(CompressionFileError):
    pass
