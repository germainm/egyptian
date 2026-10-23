from .literals import (
    COLOR_CONTRAST_DARK, COLOR_CONTRAST_LIGHT, COLOR_LUMINANCE_THRESHOLD
)


def get_color_channel_luminance(value):
    if value <= 0.04045:
        return value / 12.92
    else:
        return ((value + 0.055) / 1.055) ** 2.4


def get_color_luminance(color):
    color = color.strip().lstrip('#')

    if len(color) == 3:
        color = ''.join(
            character * 2 for character in color
        )

    if len(color) != 6:
        raise ValueError(
            'Unsupported hexadecimal color notation: {}'.format(color)
        )

    red, green, blue = (
        get_color_channel_luminance(
            value=int(
                color[index:index + 2], base=16
            ) / 255
        ) for index in (0, 2, 4)
    )

    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def get_color_contrast(color):
    try:
        luminance = get_color_luminance(color=color)
    except (AttributeError, ValueError):
        return COLOR_CONTRAST_LIGHT

    if luminance > COLOR_LUMINANCE_THRESHOLD:
        return COLOR_CONTRAST_DARK
    else:
        return COLOR_CONTRAST_LIGHT
