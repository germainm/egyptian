def setting_value_to_optional_int(value):
    if value in ('', None):
        return value

    return int(value)
