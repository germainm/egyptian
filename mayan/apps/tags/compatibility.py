from django.db import models


class RGBColorField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 7
        super().__init__(*args, **kwargs)
