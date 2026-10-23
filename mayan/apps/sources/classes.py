from mayan.apps.common.class_mixins import AppsModuleLoaderMixin


class DocumentCreateWizardStep(AppsModuleLoaderMixin):
    _deregistry = {}
    _loader_module_name = 'wizard_steps'
    _registry = {}

    @classmethod
    def deregister(cls, step):
        cls._deregistry[step.name] = step

    @classmethod
    def deregister_all(cls):
        for step in cls.get_all():
            cls.deregister(step=step)

    @classmethod
    def done(cls, wizard):
        return {}

    @classmethod
    def get(cls, name):
        for step in cls.get_all():
            if name == step.name:
                return step

        raise KeyError(
            'Wizard step `{}` not found.'.format(name)
        )

    @classmethod
    def get_all(cls):
        step_list = [
            step for step in cls._registry.values() if step.name not in cls._deregistry
        ]

        return sorted(step_list, key=lambda entry: entry.number)

    @classmethod
    def get_choices(cls, attribute_name):
        return [
            (
                step.name, getattr(step, attribute_name)
            ) for step in cls.get_all()
        ]

    @classmethod
    def get_form_initial(cls, wizard):
        return {}

    @classmethod
    def get_form_kwargs(cls, wizard):
        return {}

    @classmethod
    def get_next_is_enabled(cls, wizard):
        return True

    @classmethod
    def post_upload_process(
        cls, document, query_string, source_id, user_id
    ):
        for step in cls.get_all():
            step.step_post_upload_process(
                document=document, query_string=query_string,
                source_id=source_id, user_id=user_id
            )

    @classmethod
    def register(cls, step):
        if step.name in cls._registry:
            raise Exception(
                'A step with this name already exists: %s' % step.name
            )

        if step.number in [reigstered_step.number for reigstered_step in cls.get_all()]:
            raise Exception(
                'A step with this number already exists: %s' % step.name
            )

        cls._registry[step.name] = step

    @classmethod
    def reregister(cls, name):
        cls._deregistry.pop(name)

    @classmethod
    def reregister_all(cls):
        cls._deregistry = {}

    @classmethod
    def step_post_upload_process(
        cls, document, query_string, source_id, user_id
    ):
        pass
