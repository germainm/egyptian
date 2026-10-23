from django.db.models.signals import post_delete, post_save


class TemplateCacheSourceMixin:
    _template_cache_token = 0

    def do_template_cache_invalidate(self):
        template_cache_token = self.get_template_cache_token()

        self._template_cache_token = template_cache_token + 1

    def get_template_cache_token(self):
        return self._template_cache_token


class TemplateCacheSourceModel(TemplateCacheSourceMixin):
    def __init__(self, model):
        self.model = model

        model_label = model._meta.label_lower

        post_delete.connect(
            dispatch_uid='views_template_cache_source_model_post_delete_{}'.format(
                model_label
            ), receiver=self.handler_model_write, sender=model, weak=False
        )
        post_save.connect(
            dispatch_uid='views_template_cache_source_model_post_save_{}'.format(
                model_label
            ), receiver=self.handler_model_write, sender=model, weak=False
        )

    def handler_model_write(self, sender, **kwargs):
        self.do_template_cache_invalidate()


class TemplateCacheSourceRegistry:
    _source_list = []
    _source_model_dict = {}

    @classmethod
    def get_template_cache_token(cls):
        token_list = []

        for source in cls._source_list:
            source_token = source.get_template_cache_token()
            token_list.append(source_token)

        return tuple(token_list)

    @classmethod
    def register(cls, source):
        cls._source_list.append(source)

    @classmethod
    def register_model(cls, model):
        model_label = model._meta.label_lower

        try:
            return cls._source_model_dict[model_label]
        except KeyError:
            source = TemplateCacheSourceModel(model=model)

            cls._source_model_dict[model_label] = source
            cls.register(source=source)

            return source
