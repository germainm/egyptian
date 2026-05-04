from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _

from mayan.apps.acls.classes import ModelPermission
from mayan.apps.acls.permissions import (
    permission_acl_edit, permission_acl_view
)
from mayan.apps.app_manager.apps import MayanAppConfig
from mayan.apps.common.menus import (
    menu_multi_item, menu_object, menu_return, menu_secondary, menu_setup
)
from mayan.apps.events.classes import EventModelRegistry, ModelEventType
from mayan.apps.navigation.source_columns import SourceColumn

from .classes import AppImageErrorImage
from .events import event_asset_edited
from .handlers import handler_create_asset_cache
from .links import (
    link_asset_create, link_asset_delete_multiple, link_asset_delete_single,
    link_asset_edit, link_asset_list, link_asset_setup,
    link_transformation_delete_multiple, link_transformation_delete_single,
    link_transformation_edit, link_transformation_select
)
from .literals import IMAGE_ERROR_BROKEN_FILE
from .permissions import (
    permission_asset_delete, permission_asset_edit, permission_asset_view
)


class ConverterApp(MayanAppConfig):
    app_namespace = 'converter'
    app_url = 'converter'
    has_rest_api = True
    has_static_media = True
    has_tests = True
    name = 'mayan.apps.converter'
    verbose_name = _(message='Converter')

    def ready(self):
        super().ready()

        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except ImportError:
            pass

        Asset = self.get_model(model_name='Asset')
        LayerTransformation = self.get_model(
            model_name='LayerTransformation'
        )

        AppImageErrorImage(
            name=IMAGE_ERROR_BROKEN_FILE,
            template_name='converter/errors/broken_file.html'
        )
        EventModelRegistry.register(model=Asset)

        ModelEventType.register(
            model=Asset, event_types=(
                event_asset_edited,
            )
        )

        ModelPermission.register(
            model=Asset, permissions=(
                permission_acl_edit, permission_acl_view,
                permission_asset_delete, permission_asset_edit,
                permission_asset_view
            )
        )

        ModelPermission.register_inheritance(
            model=LayerTransformation,
            related='object_layer__content_object'
        )

        SourceColumn(
            attribute='label', is_identifier=True,
            is_object_absolute_url=True, is_sortable=True, source=Asset
        )
        SourceColumn(
            attribute='internal_name', include_label=True,
            is_object_absolute_url=True, is_sortable=True, source=Asset
        )

        SourceColumn(
            attribute='order', is_identifier=True, is_sortable=True,
            source=LayerTransformation
        )
        SourceColumn(
            func=lambda context: str(
                context['object']
            ), include_label=True, label=_(message='Transformation'),
            source=LayerTransformation
        )
        SourceColumn(
            attribute='get_arguments_column', include_label=True,
            source=LayerTransformation
        )

        menu_multi_item.bind_links(
            links=(link_asset_delete_multiple,), sources=(Asset,)
        )
        menu_object.bind_links(
            links=(
                link_asset_delete_single, link_asset_edit
            ), sources=(Asset,)
        )
        menu_return.bind_links(
            links=(link_asset_list,),
            sources=(
                Asset, 'converter:asset_list', 'converter:asset_create',
                'converter:asset_multiple_delete'
            )
        )
        menu_secondary.bind_links(
            links=(link_asset_create,),
            sources=(
                Asset, 'converter:asset_list', 'converter:asset_create',
                'converter:asset_multiple_delete'
            )
        )
        menu_setup.bind_links(
            links=(link_asset_setup,)
        )

        menu_multi_item.bind_links(
            links=(link_transformation_delete_multiple,),
            sources=(LayerTransformation,)
        )

        menu_object.bind_links(
            links=(
                link_transformation_edit, link_transformation_delete_single
            ), sources=(LayerTransformation,)
        )
        menu_secondary.bind_links(
            links=(link_transformation_select,),
            sources=(LayerTransformation,)
        )
        menu_secondary.bind_links(
            links=(link_transformation_select,),
            sources=(
                'converter:transformation_create',
                'converter:transformation_list'
            )
        )

        post_migrate.connect(
            dispatch_uid='converter_handler_create_asset_cache',
            receiver=handler_create_asset_cache
        )
