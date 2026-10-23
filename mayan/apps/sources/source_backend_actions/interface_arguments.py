class SourceBackendActionInterfaceArgument:
    def __eq__(self, other):
        return self.name == other.name

    def __init__(
        self, choices=None, help_text=None, hidden=False, required=True,
        **kwargs
    ):
        try:
            self.default = kwargs.pop('default')
        except KeyError:
            self.has_default = False
        else:
            self.has_default = True

        self.choices = choices
        self.help_text = help_text
        self.hidden = hidden
        self.required = required
