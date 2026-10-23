from django.utils.translation import gettext_lazy as _

from mayan.apps.navigation.links import Link, Separator
from mayan.apps.navigation.utils import get_content_type_kwargs_factory

from .icons import (
    icon_about, icon_book, icon_documentation, icon_forum,
    icon_knowledge_base, icon_license, icon_mailing_list, icon_object_copy,
    icon_release_notes, icon_setup, icon_source_code, icon_store,
    icon_support, icon_tools, icon_trademark_policy
)
from .literals import (
    URL_BOOK, URL_DOCUMENTATION, URL_FORUM, URL_KNOWLEDGE_BASE,
    URL_MAILING_LIST, URL_RELEASE_NOTES, URL_SOURCE_CODE, URL_STORE,
    URL_SUPPORT
)
from .permissions import permission_object_copy


def object_copy_conditional_disable(context, resolved_object):
    from .classes import ModelCopy

    if not resolved_object:
        return False
    else:
        try:
            return ModelCopy.get(
                model=resolved_object._meta.model
            ).test_condition(instance=resolved_object)
        except KeyError:
            return False


link_about = Link(
    icon=icon_about, text=_(message='About this'), view='common:about_view'
)
link_book = Link(
    icon=icon_book, tags='new_window', text=_(message='Get the book'),
    url=URL_BOOK
)
link_documentation = Link(
    icon=icon_documentation, tags='new_window',
    text=_(message='Documentation'), url=URL_DOCUMENTATION
)
link_forum = Link(
    icon=icon_forum, tags='new_window', text=_(message='Forum'),
    url=URL_FORUM
)
link_knowledge_base = Link(
    icon=icon_knowledge_base, tags='new_window',
    text=_(message='Knowledge base'), url=URL_KNOWLEDGE_BASE
)
link_license = Link(
    icon=icon_license, text=_(message='License'), view='common:license_view'
)
link_trademark_policy = Link(
    icon=icon_trademark_policy, text=_(message='Trademark policy'),
    view='common:trademark_policy_view'
)
link_mailing_list = Link(
    icon=icon_mailing_list, tags='new_window',
    text=_(message='Mailing list'), url=URL_MAILING_LIST
)
link_object_copy = Link(
    condition=object_copy_conditional_disable,
    icon=icon_object_copy, kwargs=get_content_type_kwargs_factory(),
    text=_(message='Copy'), permission=permission_object_copy,
    view='common:object_copy'
)
link_release_notes = Link(
    icon=icon_release_notes, tags='new_window',
    text=_(message='Release notes'), url=URL_RELEASE_NOTES
)
link_separator_information = Separator()
link_setup = Link(
    icon=icon_setup, text=_(message='Setup'), view='common:setup_list'
)
link_source_code = Link(
    icon=icon_source_code, tags='new_window', text=_(message='Source code'),
    url=URL_SOURCE_CODE
)
link_store = Link(
    icon=icon_store, tags='new_window', text=_(message='Online store'),
    url=URL_STORE
)
link_support = Link(
    icon=icon_support, tags='new_window', text=_(message='Support'),
    url=URL_SUPPORT
)
link_tools = Link(
    icon=icon_tools, text=_(message='Tools'), view='common:tools_list'
)
