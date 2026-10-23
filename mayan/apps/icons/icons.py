from django.template.loader import get_template


class IconDriver:
    context = {}
    _registry = {}

    @classmethod
    def get(cls, name):
        return cls._registry[name]

    @classmethod
    def register(cls, driver_class):
        cls._registry[driver_class.name] = driver_class

    def get_context(self):
        return self.context

    def render(self, extra_context=None):
        context = self.get_context()
        if extra_context:
            context.update(extra_context)

        template = get_template(template_name=self.template_name)

        return template.render(context=context)


class FontAwesomeDriver(IconDriver):
    name = 'fontawesome'
    template_name = 'icons/font_awesome/symbol.html'

    def __init__(self, symbol, css_classes=None, style=None):
        self.css_classes = css_classes or ''
        self.style = style or 'fa-solid'
        self.symbol = symbol

    def get_context(self):
        return {
            'css_classes': self.css_classes, 'style': self.style,
            'symbol': self.symbol
        }


class FontAwesomeDualDriver(IconDriver):
    name = 'fontawesome-dual'
    template_name = 'icons/font_awesome/layers.html'

    def __init__(self, primary_symbol, secondary_symbol):
        self.primary_symbol = primary_symbol
        self.secondary_symbol = secondary_symbol

    def get_context(self):
        return {
            'wrapper_css_classes': 'mayan-icon-dual',
            'data': (
                {
                    'class': 'fa-solid fa-circle',
                    'transform': 'shrink-2 down-4 right-6',
                    'mask': 'fa-solid fa-{}'.format(self.primary_symbol)
                },
                {
                    'class': 'fa-regular fa-circle',
                    'transform': 'shrink-2 down-4 right-6'
                },
                {
                    'class': 'fa-solid fa-{}'.format(self.secondary_symbol),
                    'transform': 'shrink-8 down-4 right-6'
                }
            )
        }


class FontAwesomeLayersDriver(IconDriver):
    name = 'fontawesome-layers'
    template_name = 'icons/font_awesome/layers.html'

    def __init__(self, data):
        self.data = data

    def get_context(self):
        return {'data': self.data}


class Icon:
    def __init__(self, driver_name, **kwargs):
        self.kwargs = kwargs
        self.driver = IconDriver.get(name=driver_name)(**kwargs)

    def render(self, **kwargs):
        return self.driver.render(**kwargs)


IconDriver.register(driver_class=FontAwesomeDriver)
IconDriver.register(driver_class=FontAwesomeDualDriver)
IconDriver.register(driver_class=FontAwesomeLayersDriver)
