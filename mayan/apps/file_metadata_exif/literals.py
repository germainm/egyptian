import platform

if platform.system() in ('FreeBSD', 'OpenBSD', 'Darwin'):
    DEFAULT_EXIF_PATH = '/usr/local/bin/exiftool'
else:
    DEFAULT_EXIF_PATH = '/usr/bin/exiftool'

DEFAULT_EXIF_TIMEOUT = 60
