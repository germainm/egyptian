from .literals import SETTING_VALUE_BOOLEAN_MAP


def setting_value_to_boolean(value):
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        if value in (0, 1):
            return bool(value)
    elif isinstance(value, str):
        value_normalized = value.strip().lower()

        try:
            return SETTING_VALUE_BOOLEAN_MAP[value_normalized]
        except KeyError:
            """
            Not a recognized boolean notation. Reported by the error below.
            """

    raise ValueError(
        'the value `{}` is not a boolean; use `true` or `false`.'.format(
            value
        )
    )


DATA_TYPE_FUNCTION_MAP = {
    bool: setting_value_to_boolean
}
