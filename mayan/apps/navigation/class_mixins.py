import logging

from django.template import VariableDoesNotExist

from mayan.apps.views.utils import get_request_from_context

logger = logging.getLogger(name=__name__)


class TemplateObjectMixin:
    def check_condition(self, context, resolved_object=None):
        if self.condition:
            return self.condition(
                context=context, resolved_object=resolved_object
            )
        else:
            return True

    def get_request(self, context, request=None):
        if not request:
            try:
                request = get_request_from_context(context=context)
            except VariableDoesNotExist:
                logger.warning(
                    'No request variable, aborting `{}` '
                    'resolution'.format(self.__class__.__name__)
                )
                raise

        return request
