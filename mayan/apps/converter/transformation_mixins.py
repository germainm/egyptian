import logging

from PIL import Image, ImageColor, ImageDraw, ImageFont

from django.apps import apps
from django.utils.encoding import force_bytes
from django.utils.translation import gettext_lazy as _

from mayan.apps.forms import form_fields, form_widgets, forms

from .literals import DEFAULT_TEXT_FONT_SIZE

logger = logging.getLogger(name=__name__)


class ImagePasteTransformationMixin:
    class Form(forms.Form):
        rotation = form_fields.IntegerField(
            help_text=_(
                message='Number of degrees to rotate the image counter '
                'clockwise around its center.'
            ), label=_(message='Rotation'), required=False
        )
        transparency = form_fields.FloatField(
            help_text=_(message='Opacity level of the image in percent'),
            label=_(message='Transparency'), required=False
        )
        zoom = form_fields.FloatField(
            help_text=_(message='Zoom level in percent.'),
            label=_(message='Zoom'), required=False
        )

    @classmethod
    def get_arguments(cls):
        arguments = super().get_arguments() + (
            'rotation', 'transparency', 'zoom'
        )
        return arguments

    def _update_hash(self):
        result = super()._update_hash()
        instance = self.get_model_instance()
        result.update(
            force_bytes(
                s=instance.get_hash()
            )
        )

        return result

    def execute_on(self, *args, **kwargs):
        super().execute_on(*args, **kwargs)
        return self._execute_on(*args, **kwargs)

    def get_image(self):
        instance = self.get_model_instance()

        return instance.get_image()

    def get_images(self):
        try:
            self.transparency = float(self.transparency or '100.0')
        except ValueError:
            self.transparency = 100

        if self.transparency < 0:
            self.transparency = 0
        elif self.transparency > 100:
            self.transparency = 100

        try:
            self.rotation = int(self.rotation or '0') % 360
        except ValueError:
            self.rotation = 0

        try:
            self.zoom = float(self.zoom or '100.0')
        except ValueError:
            self.zoom = 100.0

        instance_image = self.get_image()

        if instance_image.mode != 'RGBA':
            instance_image.putalpha(alpha=255)

        instance_image = instance_image.rotate(
            angle=360 - self.rotation, resample=Image.Resampling.BICUBIC,
            expand=True
        )

        if self.zoom != 100.0:
            zoom_decimal_value = self.zoom / 100.0
            instance_image = instance_image.resize(
                size=(
                    int(instance_image.size[0] * zoom_decimal_value),
                    int(instance_image.size[1] * zoom_decimal_value)
                ), resample=Image.Resampling.LANCZOS
            )

        paste_mask = instance_image.getchannel(channel='A').point(
            lut=lambda pixel: int(pixel * self.transparency / 100)
        )

        return {'instance_image': instance_image, 'paste_mask': paste_mask}


class ImagePasteCoordinatesAbsoluteTransformationMixin(
    ImagePasteTransformationMixin
):
    arguments = ('left', 'top')
    label = _(message='Paste an image')
    name = 'paste_image'

    class Form(ImagePasteTransformationMixin.Form):
        left = form_fields.IntegerField(
            help_text=_(
                message='Horizontal position in pixels from the left.'
            ), label=_(message='Left'), required=False
        )
        top = form_fields.IntegerField(
            help_text=_(message='Vertical position in pixels from the top.'),
            label=_(message='Top'), required=False
        )

    def _execute_on(self, *args, **kwargs):
        try:
            self.left = int(self.left or '0')
        except ValueError:
            self.left = 0

        try:
            self.top = int(self.top or '0')
        except ValueError:
            self.top = 0

        if self.left < 0:
            self.left = 0

        if self.top < 0:
            self.top = 0

        images = self.get_images()

        self.image.paste(
            box=(self.left, self.top), im=images['instance_image'],
            mask=images['paste_mask']
        )

        return self.image


class ImagePasteCoordinatesPercentTransformationMixin(
    ImagePasteTransformationMixin
):
    arguments = ('left', 'top')
    label = _(message='Paste an image (percent coordinates)')
    name = 'paste_image_percent'

    class Form(ImagePasteTransformationMixin.Form):
        left = form_fields.FloatField(
            help_text=_(
                message='Horizontal position in percent from the left.'
            ), label=_(message='Left'), required=False
        )
        top = form_fields.FloatField(
            help_text=_(
                message='Vertical position in percent from the top.'
            ), label=_(message='Top'), required=False
        )

    def _execute_on(self, *args, **kwargs):
        try:
            self.left = float(self.left or '0')
        except ValueError:
            self.left = 0

        try:
            self.top = float(self.top or '0')
        except ValueError:
            self.top = 0

        if self.left < 0:
            self.left = 0

        if self.left > 100:
            self.left = 100

        if self.top < 0:
            self.top = 0

        if self.top > 100:
            self.top = 100

        images = self.get_images()

        base_width, base_height = self.image.size
        image_width, image_height = images['instance_image'].size

        self.left = int(
            self.left / 100.0 * (base_width - image_width)
        )
        self.top = int(
            self.top / 100.0 * (base_height - image_height)
        )

        self.image.paste(
            box=(self.left, self.top), im=images['instance_image'],
            mask=images['paste_mask']
        )

        return self.image


class ImageWatermarkPercentTransformationMixin(
    ImagePasteTransformationMixin
):
    arguments = (
        'left', 'top', 'right', 'bottom', 'horizontal_increment',
        'vertical_increment'
    )
    label = _(message='Paste an asset as watermark')
    name = 'paste_asset_watermark'

    class Form(ImagePasteTransformationMixin.Form):
        left = form_fields.IntegerField(
            help_text=_(
                message='Horizontal start position in pixels from the left.'
            ), label=_(message='Left'), required=False
        )
        right = form_fields.IntegerField(
            help_text=_(
                message='Horizontal end position in pixels from the right.'
            ), label=_(message='Right'), required=False
        )
        top = form_fields.IntegerField(
            help_text=_(
                message='Vertical start position in pixels from the top.'
            ), label=_(message='Top'), required=False
        )
        bottom = form_fields.IntegerField(
            help_text=_(
                message='Vertical end position in pixels from the top.'
            ), label=_(message='Bottom'), required=False
        )
        horizontal_increment = form_fields.IntegerField(
            help_text=_(message='Horizontal position increments in pixels.'),
            label=_(message='Horizontal increment'), required=False
        )
        vertical_increment = form_fields.IntegerField(
            help_text=_(message='Vertical position increments in pixels.'),
            label=_(message='Vertical increment'), required=False
        )

    def _execute_on(self, *args, **kwargs):
        try:
            self.left = int(self.left or '0')
        except ValueError:
            self.left = 0

        try:
            self.top = int(self.top or '0')
        except ValueError:
            self.top = 0

        try:
            self.right = int(self.right or '0')
        except ValueError:
            self.right = 0

        try:
            self.bottom = int(self.bottom or '0')
        except ValueError:
            self.bottom = 0

        images = self.get_images()

        try:
            self.horizontal_increment = int(self.horizontal_increment or '0')
        except ValueError:
            self.horizontal_increment = 0

        try:
            self.vertical_increment = int(self.vertical_increment or '0')
        except ValueError:
            self.vertical_increment = 0

        if self.horizontal_increment == 0:
            self.horizontal_increment = images['paste_mask'].size[0]

        if self.vertical_increment == 0:
            self.vertical_increment = images['paste_mask'].size[1]

        for x in range(self.left, self.right or self.image.size[0], self.horizontal_increment):
            for y in range(self.top, self.bottom or self.image.size[1], self.vertical_increment):
                self.image.paste(
                    box=(x, y), im=images['instance_image'],
                    mask=images['paste_mask']
                )

        return self.image


class TransformationDrawTextMixin(ImagePasteTransformationMixin):
    @classmethod
    def get_arguments(cls):
        arguments = super().get_arguments() + (
            'text', 'font_size', 'font_color'
        )
        return arguments

    @classmethod
    def get_form_class(cls):
        SuperForm = super().get_form_class()

        class FormWithText(SuperForm):
            text = form_fields.CharField(
                help_text=_(message='Text to draw on the image.'),
                label=_(message='Text'), required=True
            )
            font_size = form_fields.IntegerField(
                help_text=_(message='Size of the text in pixels.'),
                initial=DEFAULT_TEXT_FONT_SIZE,
                label=_(message='Font size'), required=False
            )
            font_color = form_fields.CharField(
                help_text=_(message='Color used to draw the text.'),
                label=_(message='Font color'), required=False,
                widget=form_widgets.ColorWidget()
            )

        return FormWithText

    def _update_hash(self):
        result = super(
            ImagePasteTransformationMixin, self
        )._update_hash()

        for value in (self.text, self.font_size, self.font_color):
            result.update(
                force_bytes(s=value)
            )

        return result

    def get_image(self):
        text = self.text or ''

        try:
            font_size = int(self.font_size or DEFAULT_TEXT_FONT_SIZE)
        except (TypeError, ValueError):
            font_size = DEFAULT_TEXT_FONT_SIZE

        if font_size < 1:
            font_size = DEFAULT_TEXT_FONT_SIZE

        font_color_value = getattr(self, 'font_color', None)
        if font_color_value and font_color_value != 'None':
            fill_color = ImageColor.getrgb(color=font_color_value)
        else:
            fill_color = (0, 0, 0)

        fill_color += (255,)

        font = ImageFont.load_default(size=font_size)

        measure_draw = ImageDraw.Draw(
            im=Image.new(mode='RGBA', size=(1, 1))
        )
        left, top, right, bottom = measure_draw.multiline_textbbox(
            font=font, text=text, xy=(0, 0)
        )

        width = max(right - left, 1)
        height = max(bottom - top, 1)

        text_image = Image.new(
            color=(0, 0, 0, 0), mode='RGBA', size=(width, height)
        )
        draw = ImageDraw.Draw(im=text_image)
        draw.multiline_text(
            fill=fill_color, font=font, text=text, xy=(-left, -top)
        )

        return text_image


class AssetTransformationMixin:
    @classmethod
    def get_form_class(cls):
        SuperForm = super().get_form_class()

        class FormWithSuperArguments(SuperForm):
            asset_name = form_fields.ChoiceField(
                help_text=_(message='Asset name'), label=_(message='Asset'),
                required=True
            )

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

                def get_asset_choices():
                    queryset = apps.get_model(
                        app_label='converter', model_name='Asset'
                    ).objects.all()

                    for asset in queryset.all():
                        yield (asset.internal_name, asset)

                self.fields['asset_name'].choices = get_asset_choices()

        return FormWithSuperArguments

    @classmethod
    def get_arguments(cls):
        arguments = super().get_arguments() + (
            'asset_name',
        )
        return arguments

    def get_model_instance(self):
        asset_name = getattr(self, 'asset_name', None)

        Asset = apps.get_model(app_label='converter', model_name='Asset')

        try:
            asset = Asset.objects.get(internal_name=asset_name)
        except Asset.DoesNotExist:
            logger.error('Asset "%s" not found.', asset_name)
            raise
        else:
            return asset


class TransformationDrawRectangleMixin:
    class Form(forms.Form):
        fillcolor = form_fields.CharField(
            help_text=_(message='Color used to fill the rectangle.'),
            label=_(message='Fill color'), required=False,
            widget=form_widgets.ColorWidget()
        )
        fill_transparency = form_fields.IntegerField(
            help_text=_(
                message='Opacity level of the fill color in percent'
            ), label=_(message='Fill transparency'), required=False
        )
        outlinecolor = form_fields.CharField(
            help_text=_(
                message='Color used for the outline of the rectangle.'
            ), label=_(message='Outline color'), required=False,
            widget=form_widgets.ColorWidget()
        )
        outlinewidth = form_fields.CharField(
            help_text=_(message='Width in pixels of the rectangle outline.'),
            label=_(message='Outline width'), required=False
        )

    def _execute_on(self, *args, **kwargs):
        fillcolor_value = getattr(self, 'fillcolor', None)
        if fillcolor_value:
            fill_color = ImageColor.getrgb(color=fillcolor_value)
        else:
            fill_color = (0, 0, 0)

        try:
            fill_transparency = int(
                getattr(self, 'fill_transparency', None) or '0'
            )
        except ValueError:
            fill_transparency = 100
        else:
            if fill_transparency < 0:
                fill_transparency = 0
            elif fill_transparency > 100:
                fill_transparency = 100

        opacity = int(
            (100 - fill_transparency) / 100 * 255
        )

        fill_color += (opacity,)

        outlinecolor_value = getattr(self, 'outlinecolor', None)
        if outlinecolor_value:
            outline_color = ImageColor.getrgb(color=outlinecolor_value)
        else:
            outline_color = None

        outlinewidth_value = getattr(self, 'outlinewidth', None)
        if outlinewidth_value:
            outline_width = int(outlinewidth_value)
        else:
            outline_width = 0

        draw = ImageDraw.Draw(im=self.image, mode='RGBA')
        draw.rectangle(
            fill=fill_color, outline=outline_color, width=outline_width,
            xy=(self.left, self.top, self.right, self.bottom)
        )

        return self.image
