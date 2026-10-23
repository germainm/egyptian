class TemplatingError(Exception):
    pass


class DangerousTagError(TemplatingError):
    pass
