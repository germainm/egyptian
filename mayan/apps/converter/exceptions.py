class ConvertError(Exception):
    pass


class AppImageError(ConvertError):
    def __init__(self, error_name, details=None):
        self.details = details
        self.error_name = error_name
        super().__init__()

    def __str__(self):
        return (
            'Error name: {}'.format(
                repr(self.error_name)
            )
        )


class InvalidOfficeFormat(ConvertError):
    pass


class LayerError(ConvertError):
    pass


class OfficeConversionError(ConvertError):
    pass


class PageCountError(ConvertError):
    pass


class UnknownFileFormat(ConvertError):
    pass


class UnkownConvertError(ConvertError):
    pass
