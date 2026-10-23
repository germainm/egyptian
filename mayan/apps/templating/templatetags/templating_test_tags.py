from django.conf import settings
from django.template import Library

from ..decorators import templating_dangerous_tag

register = Library()

if settings.TESTING:
    from ..tests.literals import TEST_TEMPLATE_TAG_RESULT

    @register.filter(name='dangerous_filter')
    @templating_dangerous_tag()
    def templating_test_filter_dangerous(value):
        """
        Test docstring dangerous filter
        """
        return TEST_TEMPLATE_TAG_RESULT

    @register.simple_tag
    def templating_test_tag():
        """
        Test docstring
        """
        return TEST_TEMPLATE_TAG_RESULT

    @register.simple_tag(name='dangerous_tag')
    @templating_dangerous_tag()
    def templating_test_tag_dangerous():
        """
        Test docstring dangerous tag
        """
        return TEST_TEMPLATE_TAG_RESULT
