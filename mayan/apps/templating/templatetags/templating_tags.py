import base64

from django.template import Library, Node, TemplateSyntaxError
from django.utils.html import strip_spaces_between_tags
from django.utils.translation import gettext_lazy as _

from mayan.apps.common.utils import flatten_map, flatten_object

from ..decorators import templating_dangerous_tag

register = Library()



@register.filter(name='dict_get')
def filter_dict_get(dictionary, key):
    """
    Return the value for the given key or '' if not found.
    Deprecated in favor or `dictionary_get`.
    """
    return dictionary.get(key, '')


@register.filter(name='dictionary_flatten')
def filter_dictionary_flatten(dictionary):
    """
    Return a flat version of a nested dictionary.
    """
    result = {}

    flatten_map(dictionary=dictionary, result=result, separator='__')

    return result


@register.filter(name='dictionary_get')
def filter_dictionary_get(dictionary, key):
    """
    Return the value for the given key or '' if not found.
    """
    return dictionary.get(key, '')


@register.filter(name='object_flatten')
def filter_object_flatten(value):
    """
    Return a flat version of a nested object of multiple types.
    """

    result = dict(
        flatten_object(obj=value, separator='__')
    )

    return result


@register.filter(name='split')
def filter_split(obj, separator):
    """
    Return a list of the words in the string, using sep as the delimiter
    string.
    """
    return obj.split(separator)


@register.filter(name='to_base64')
def filter_to_base64(value, altchars=None):
    """
    Convert a value to base64 encoding. Accepts optional `altchars` argument.
    """
    if altchars:
        altchars = bytes(encoding='utf-8', source=altchars)
    return base64.b64encode(s=value, altchars=altchars).decode('utf-8')




class SpacelessPlusNode(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        content = self.nodelist.render(context).strip()
        result = []
        for line in content.split('\n'):
            if line.strip() != '':
                result.append(line)

        return strip_spaces_between_tags(
            value='\n'.join(result)
        )


@register.simple_tag(name='method')
@templating_dangerous_tag(
    reason=_(
        message='Tag can bypass access controls and create permanent changes.'
    )
)
def tag_method(obj, method, *args, **kwargs):
    """
    Call an object method. {% method object method **kwargs %}
    """
    try:
        return getattr(obj, method)(*args, **kwargs)
    except Exception as exception:
        raise TemplateSyntaxError(
            'Error calling object method; {}'.format(exception)
        )


@register.simple_tag(name='range')
def tag_range(*args):
    """
    Return an object that produces a sequence of integers
    """
    return range(*args)


@register.simple_tag(name='set')
def tag_set(value):
    """
    Set a context variable to a specific value.
    """
    return value


@register.tag(name='spaceless_plus')
def tag_spaceless_plus(parser, token):
    """
    Removes empty lines between the tag nodes.
    """
    nodelist = parser.parse(
        ('endspaceless_plus',)
    )
    parser.delete_first_token()
    return SpacelessPlusNode(nodelist=nodelist)
