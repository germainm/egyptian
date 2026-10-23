from datetime import datetime

from django.utils.timezone import make_aware


def do_timestamp_convert(timestamp):
    datetime_object = datetime.fromtimestamp(timestamp=timestamp)
    result = make_aware(value=datetime_object)
    return result
