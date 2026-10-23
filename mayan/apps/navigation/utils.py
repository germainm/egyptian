import logging

from django.apps import apps
from django.core.exceptions import PermissionDenied
from django.template import Variable, VariableDoesNotExist
from django.urls import Resolver404, resolve

from mayan.apps.permissions.classes import Permission

logger = logging.getLogger(name=__name__)


def factory_condition_queryset_access(
    app_label, model_name, object_permission, callback=None,
    view_permission=None
):
    def function_condition(context, resolved_object):
        AccessControlList = apps.get_model(
            app_label='acls', model_name='AccessControlList'
        )

        Model = apps.get_model(app_label=app_label, model_name=model_name)

        try:
            request = context.request
        except AttributeError:
            try:
                request = Variable(var='request').resolve(context=context)
            except VariableDoesNotExist:
                logger.warning(
                    'No request variable, aborting cascade condition.'
                )
                return ()

        user = request.user

        if view_permission:
            if user.is_authenticated:
                try:
                    Permission.check_user_permission(
                        permission=view_permission, user=user
                    )
                except PermissionDenied:
                    """
                    Don't raise an error, just ignore and let
                    .restrict_queryset() perform a fine grained filtering.
                    """
                else:
                    if callback:
                        return callback(
                            context=context, resolved_object=resolved_object
                        )
                    else:
                        return True
            else:
                return False

        if user.is_authenticated:
            queryset = AccessControlList.objects.restrict_queryset(
                permission=object_permission, queryset=Model.objects.all(),
                user=user
            )
            if callback:
                return queryset.exists() and callback(
                    context=context, resolved_object=resolved_object
                )
            else:
                return queryset.exists()
        elif callback:
            return False

    return function_condition


def get_content_type_kwargs_factory(
    result_map=None, variable_name='resolved_object'
):
    if not result_map:
        result_map = {
            'app_label': 'app_label',
            'model_name': 'model_name',
            'object_id': 'object_id'
        }

    def get_kwargs(context):
        ContentType = apps.get_model(
            app_label='contenttypes', model_name='ContentType'
        )

        content_type = ContentType.objects.get_for_model(
            model=context[variable_name]
        )
        return {
            result_map['app_label']: '"{}"'.format(content_type.app_label),
            result_map['model_name']: '"{}"'.format(content_type.model),
            result_map['object_id']: '{}.pk'.format(variable_name)
        }

    return get_kwargs


def get_current_view_name(request):
    current_path = request.META['PATH_INFO']

    try:
        current_view_name = resolve(path=current_path).view_name
    except Resolver404:
        logger.warning(
            'Can\'t figure out which view corresponds to this '
            'URL: %s; aborting menu resolution.', current_path
        )
    else:
        return current_view_name
