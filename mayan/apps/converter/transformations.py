import hashlib
import logging

from PIL import Image, ImageColor, ImageFilter
import qrcode

from django.core.exceptions import ValidationError
from django.utils.encoding import force_bytes
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from mayan.apps.forms import form_fields, form_widgets, forms
from mayan.apps.views.http import URL

from .layers import layer_decorations, layer_saved_transformations
from .transformation_mixins import (
    AssetTransformationMixin,
    ImagePasteCoordinatesAbsoluteTransformationMixin,
    ImagePasteCoordinatesPercentTransformationMixin,
    ImagePasteTransformationMixin, ImageWatermarkPercentTransformationMixin,
    TransformationDrawRectangleMixin, TransformationDrawTextMixin
)

logger = logging.getLogger(name=__name__)


class BaseTransformationType(type):
    def __str__(self):
        return str(self.label)


class BaseTransformation(metaclass=BaseTransformationType):
    _layer_transformations = {}
    _registry = {}
    arguments = ()
    name = 'base_transformation'
    template_name = None

    @staticmethod
    def combine(transformations):
        hash_object = hashlib.sha256()

        for transformation in transformations or ():
            try:
                hash_object.update(
                    transformation.cache_hash()
                )
            except Exception as exception:
                logger.error(
                    'Unable to compute hash for transformation: %s; %s',
                    transformation, exception
                )

        return hash_object.hexdigest()

    @staticmethod
    def list_as_query_string(transformation_instance_list):
        result = URL()

        for index, transformation in enumerate(transformation_instance_list):
            result.args[
                'transformation_{}_name'.format(index)
            ] = transformation.name

            for argument in transformation.arguments:
                value = getattr(transformation, argument)
                result.args[
                    'transformation_{}_argument__{}'.format(index, argument)
                ] = value

        return result.to_string()

    @classmethod
    def get(cls, name):
        return cls._registry[name]

    @classmethod
    def get_arguments(cls):
        return cls.arguments

    @classmethod
    def validate_arguments(cls, arguments):
        pass

    @classmethod
    def get_assigned_layer(cls):
        for layer, transformations in cls._layer_transformations.items():
            if cls in transformations:
                return layer

    @classmethod
    def get_form_class(cls):
        return getattr(cls, 'Form', None)

    @classmethod
    def get_label(cls):
        arguments = cls.get_arguments()
        if arguments:
            return format_lazy(
                '{}: {}', cls.label, ', '.join(arguments)
            )
        else:
            return cls.label

    @classmethod
    def get_template_name(cls):
        return cls.template_name

    @classmethod
    def get_transformation_choices(cls, group_by_layer=False, layer=None):
        if layer:
            transformation_list = [
                (
                    transformation.name, transformation
                ) for transformation in cls._layer_transformations.get(
                    layer, ()
                )
            ]
        else:
            transformation_list = cls._registry.items()

        if group_by_layer:
            flat_transformation_list = [
                klass for name, klass in transformation_list
            ]

            layer_transformation_choices = {}
            for layer, transformations in cls._layer_transformations.items():
                for transformation in transformations:
                    if transformation in flat_transformation_list:
                        layer_transformation_choices.setdefault(
                            layer, []
                        )
                        layer_transformation_choices[layer].append(
                            (
                                transformation.name,
                                transformation.get_label()
                            )
                        )

                layer_transformation_choices[layer].sort(
                    key=lambda x: x[1]
                )

            result = [
                (
                    layer.label, transformations
                ) for layer, transformations in layer_transformation_choices.items()
            ]

            return sorted(
                result, key=lambda x: x[0]
            )
        else:
            return sorted(
                (
                    name, klass.get_label()
                ) for name, klass in transformation_list
            )

    @classmethod
    def register(cls, layer, transformation):
        cls._registry[transformation.name] = transformation
        cls._layer_transformations.setdefault(
            layer, set()
        )
        cls._layer_transformations[layer].add(transformation)

    def __init__(self, **kwargs):
        self.kwargs = {}
        for argument_name in self.__class__.get_arguments():
            setattr(
                self, argument_name, kwargs.get(argument_name)
            )
            self.kwargs[argument_name] = kwargs.get(argument_name)

    def _update_hash(self):
        string = force_bytes(s=self.name)
        hash_object = hashlib.sha256(string=string)

        for key, value in sorted(self.kwargs.items()):
            hash_object.update(
                force_bytes(s=key)
            )
            hash_object.update(
                force_bytes(s=value)
            )

        return hash_object

    def cache_hash(self):
        hash_object = self._update_hash()
        string = hash_object.hexdigest()
        return force_bytes(s=string)

    def execute_on(self, image):
        self.image = image
        self.aspect = 1.0 * image.size[0] / image.size[1]


class TransformationAssetPaste(
    ImagePasteCoordinatesAbsoluteTransformationMixin,
    AssetTransformationMixin, BaseTransformation
):
    label = _(message='Paste an asset (absolute coordinates)')
    name = 'paste_asset'


class TransformationAssetPastePercent(
    ImagePasteCoordinatesPercentTransformationMixin,
    AssetTransformationMixin, BaseTransformation
):
    label = _(message='Paste an asset (percent coordinates)')
    name = 'paste_asset_percent'


class TransformationAssetWatermark(
    ImageWatermarkPercentTransformationMixin, AssetTransformationMixin,
    BaseTransformation
):
    label = _(message='Paste an asset as watermark')
    name = 'paste_asset_watermark'


class TransformationCrop(BaseTransformation):
    arguments = ('left', 'top', 'right', 'bottom',)
    label = _(message='Crop')
    name = 'crop'

    class Form(forms.Form):
        left = form_fields.IntegerField(
            help_text=_(message='Number of pixels to remove from the left.'),
            label=_(message='Left'), required=False
        )
        top = form_fields.IntegerField(
            help_text=_(message='Number of pixels to remove from the top.'),
            label=_(message='Top'), required=False
        )
        right = form_fields.IntegerField(
            help_text=_(
                message='Number of pixels to remove from the right.'
            ), label=_(message='Right'), required=False
        )
        bottom = form_fields.IntegerField(
            help_text=_(
                message='Number of pixels to remove from the bottom.'
            ), label=_(message='Bottom'), required=False
        )

    def execute_on(self, *args, **kwargs):
        super().execute_on(*args, **kwargs)

        try:
            left = int(self.left or '0')
        except ValueError:
            left = 0

        try:
            top = int(self.top or '0')
        except ValueError:
            top = 0

        try:
            right = int(self.right or '0')
        except ValueError:
            right = 0

        try:
            bottom = int(self.bottom or '0')
        except ValueError:
            bottom = 0

        if left < 0:
            left = 0

        if left > self.image.size[0] - 1:
            left = self.image.size[0] - 1

        if top < 0:
            top = 0

        if top > self.image.size[1] - 1:
            top = self.image.size[1] - 1

        if right < 0:
            right = 0

        if right > self.image.size[0] - 1:
            right = self.image.size[0] - 1

        if bottom < 0:
            bottom = 0

        if bottom > self.image.size[1] - 1:
            bottom = self.image.size[1] - 1

        right = self.image.size[0] - right
        bottom = self.image.size[1] - bottom

        if left > right:
            left = right - 1

        if top > bottom:
            top = bottom - 1

        logger.debug(
            'left: %f, top: %f, right: %f, bottom: %f', left, top, right,
            bottom
        )

        return self.image.crop(
            box=(left, top, right, bottom)
        )


class TransformationDrawRectangle(
    TransformationDrawRectangleMixin, BaseTransformation
):
    arguments = (
        'left', 'top', 'right', 'bottom', 'fillcolor', 'fill_transparency',
        'outlinecolor', 'outlinewidth'
    )
    label = _(message='Draw rectangle')
    name = 'draw_rectangle'

    class Form(TransformationDrawRectangleMixin.Form):
        left = form_fields.IntegerField(
            help_text=_(message='Left side location in pixels.'),
            label=_(message='Left'), required=False
        )
        top = form_fields.IntegerField(
            help_text=_(message='Top side location in pixels.'),
            label=_(message='Top'), required=False
        )
        right = form_fields.IntegerField(
            help_text=_(message='Right side location in pixels.'),
            label=_(message='Right'), required=False
        )
        bottom = form_fields.IntegerField(
            help_text=_(message='Bottom side location in pixels.'),
            label=_(message='Bottom'), required=False
        )

    def execute_on(self, *args, **kwargs):
        super().execute_on(*args, **kwargs)

        try:
            left = int(self.left or '0')
        except ValueError:
            left = 0

        try:
            top = int(self.top or '0')
        except ValueError:
            top = 0

        try:
            right = int(self.right or '0')
        except ValueError:
            right = 0

        try:
            bottom = int(self.bottom or '0')
        except ValueError:
            bottom = 0

        if left < 0:
            left = 0

        if left > self.image.size[0] - 1:
            left = self.image.size[0] - 1

        if top < 0:
            top = 0

        if top > self.image.size[1] - 1:
            top = self.image.size[1] - 1

        if right < 0:
            right = 0

        if right > self.image.size[0] - 1:
            right = self.image.size[0] - 1

        if bottom < 0:
            bottom = 0

        if bottom > self.image.size[1] - 1:
            bottom = self.image.size[1] - 1

        right = self.image.size[0] - right
        bottom = self.image.size[1] - bottom

        if left > right:
            left = right - 1

        if top > bottom:
            top = bottom - 1

        self.bottom = bottom
        self.left = left
        self.top = top
        self.right = right

        return super()._execute_on(*args, **kwargs)


class TransformationDrawRectanglePercent(
    TransformationDrawRectangleMixin, BaseTransformation
):
    arguments = (
        'left', 'top', 'right', 'bottom', 'fillcolor', 'fill_transparency',
        'outlinecolor', 'outlinewidth'
    )
    label = _(message='Draw rectangle (percent coordinates)')
    name = 'draw_rectangle_percent'

    @classmethod
    def validate_arguments(cls, arguments):
        error_list = []

        pair_list = (
            ('left', 'right'), ('top', 'bottom')
        )

        for name_start, name_end in pair_list:
            value_start = arguments.get(name_start)
            value_end = arguments.get(name_end)

            if value_start is None or value_end is None:
                continue

            try:
                total = float(value_start) + float(value_end)
            except (TypeError, ValueError):
                continue

            if total >= 100:
                error_list.append(
                    _(
                        message='The "%(name_start)s" and "%(name_end)s" '
                        'values leave no area to draw. Together they must '
                        'be less than 100.'
                    ) % {
                        'name_end': name_end, 'name_start': name_start
                    }
                )

        if error_list:
            raise ValidationError(message=error_list)

    class Form(TransformationDrawRectangleMixin.Form):
        left = form_fields.FloatField(
            help_text=_(message='Left side location in percent.'),
            label=_(message='Left'), required=False
        )
        top = form_fields.FloatField(
            help_text=_(message='Top side location in percent.'),
            label=_(message='Top'), required=False
        )
        right = form_fields.FloatField(
            help_text=_(message='Right side location in percent.'),
            label=_(message='Right'), required=False
        )
        bottom = form_fields.FloatField(
            help_text=_(message='Bottom side location in percent.'),
            label=_(message='Bottom'), required=False
        )

    def execute_on(self, *args, **kwargs):
        super().execute_on(*args, **kwargs)

        try:
            left = float(self.left or '0')
        except ValueError:
            left = 0

        try:
            top = float(self.top or '0')
        except ValueError:
            top = 0

        try:
            right = float(self.right or '0')
        except ValueError:
            right = 0

        try:
            bottom = float(self.bottom or '0')
        except ValueError:
            bottom = 0

        if left < 0:
            left = 0

        if left > 100:
            left = 100

        if top < 0:
            top = 0

        if top > 100:
            top = 100

        if right < 0:
            right = 0

        if right > 100:
            right = 100

        if bottom < 0:
            bottom = 0

        if bottom > 100:
            bottom = 100

        logger.debug(
            'left: %f, top: %f, right: %f, bottom: %f', left, top, right,
            bottom
        )

        left = left / 100.0 * self.image.size[0]
        top = top / 100.0 * self.image.size[1]


        right = self.image.size[0] - (
            right / 100.0 * self.image.size[0]
        )
        bottom = self.image.size[1] - (
            bottom / 100.0 * self.image.size[1]
        )

        self.bottom = bottom
        self.left = left
        self.top = top
        self.right = right

        return super()._execute_on(*args, **kwargs)


class TransformationDrawText(
    ImagePasteCoordinatesAbsoluteTransformationMixin,
    TransformationDrawTextMixin, BaseTransformation
):
    label = _(message='Draw text (absolute coordinates)')
    name = 'draw_text'


class TransformationDrawTextPercent(
    ImagePasteCoordinatesPercentTransformationMixin,
    TransformationDrawTextMixin, BaseTransformation
):
    label = _(message='Draw text (percent coordinates)')
    name = 'draw_text_percent'


class TransformationFlip(BaseTransformation):
    arguments = ()
    label = _(message='Flip')
    name = 'flip'

    def execute_on(self, *args, **kwargs):
        super().execute_on(*args, **kwargs)

        return self.image.transpose(method=Image.FLIP_TOP_BOTTOM)


class TransformationGaussianBlur(BaseTransformation):
    arguments = ('radius',)
    label = _(message='Gaussian blur')
    name = 'gaussianblur'

    class Form(forms.Form):
        radius = form_fields.IntegerField(
            initial=2, label=_(message='Radius'), required=True
        )

    def execute_on(self, *args, **kwargs):
        super().execute_on(*args, **kwargs)

        return self.image.filter(
            filter=ImageFilter.GaussianBlur(radius=self.radius)
        )


class TransformationLineArt(BaseTransformation):
    label = _(message='Line art')
    name = 'lineart'

    def execute_on(self, *args, **kwargs):
        super().execute_on(*args, **kwargs)

        def lut(x):
            return 0 if x < 128 else 255

        return self.image.convert(mode='L').point(lut=lut, mode='1')


class TransformationMirror(BaseTransformation):
    arguments = ()
    label = _(message='Mirror')
    name = 'mirror'

    def execute_on(self, *args, **kwargs):
        super().execute_on(*args, **kwargs)

        return self.image.transpose(method=Image.FLIP_LEFT_RIGHT)


class TransformationQRCodePercent(
    ImagePasteCoordinatesPercentTransformationMixin,
    BaseTransformation
):
    label = _(message='Draw a QRCode (percent coordinates)')
    name = 'qr_code_percent'

    @classmethod
    def get_arguments(cls):
        arguments = super().get_arguments() + ('code_value',)
        return arguments

    class Form(ImagePasteCoordinatesPercentTransformationMixin.Form):
        code_value = form_fields.CharField(
            help_text=_(message='Value to encode in the QRCode.'),
            label=_(message='Code value'), required=True
        )

    def _update_hash(self):
        result = super(ImagePasteTransformationMixin, self)._update_hash()
        bytes_code_value = force_bytes(s=self.code_value)
        result.update(bytes_code_value)

        return result

    def get_image(self):
        qrcode_instance = qrcode.QRCode()
        qrcode_instance.add_data(data=self.code_value)
        qrcode_instance.make(fit=True)

        qrcode_image = qrcode_instance.make_image()

        image = qrcode_image.get_image()
        image = image.convert(mode='RGB')

        return image


class TransformationResize(BaseTransformation):
    arguments = ('width', 'height')
    label = _(message='Resize')
    name = 'resize'

    class Form(forms.Form):
        width = form_fields.IntegerField(
            help_text=_(
                message='New width in pixels.'
            ), label=_(message='Width'), required=True
        )
        height = form_fields.IntegerField(
            help_text=_(
                message='New height in pixels.'
            ), label=_(message='Height'), required=False
        )

    def execute_on(self, *args, **kwargs):
        super().execute_on(*args, **kwargs)

        width = int(self.width)
        if width < 1:
            width = 1

        height = int(
            self.height or (1.0 * width / self.aspect)
        )
        if height < 1:
            height = 1

        factor = 1
        while self.image.size[0] / factor > 2 * width and self.image.size[1] / factor > 2 * height:
            factor *= 2

        if factor > 1:
            self.image.thumbnail(
                size=(
                    self.image.size[0] / factor,
                    self.image.size[1] / factor
                ), resample=Image.Resampling.NEAREST
            )

        self.image.thumbnail(
            size=(width, height), resample=Image.Resampling.LANCZOS
        )

        return self.image


class TransformationRotate(BaseTransformation):
    arguments = ('degrees', 'fillcolor')
    label = _(message='Rotate')
    name = 'rotate'

    class Form(forms.Form):
        degrees = form_fields.IntegerField(
            help_text=_(
                message='Number of degrees to rotate the image counter '
                'clockwise around its center.'
            ), label=_(message='Degrees'), required=True
        )
        fillcolor = form_fields.CharField(
            help_text=_(
                message='Color to be used for area outside of the rotated '
                'image.'
            ), label=_(message='Fill color'), required=False,
            widget=form_widgets.ColorWidget()
        )

    def execute_on(self, *args, **kwargs):
        super().execute_on(*args, **kwargs)

        self.degrees = float(self.degrees or '0')
        self.degrees %= 360

        if self.degrees == 0:
            return self.image

        fillcolor_value = getattr(self, 'fillcolor', None)
        if fillcolor_value == 'None':
            fillcolor_value = None

        if fillcolor_value:
            fillcolor = ImageColor.getrgb(color=fillcolor_value)
        else:
            fillcolor = None

        return self.image.rotate(
            angle=360 - self.degrees, expand=True, fillcolor=fillcolor,
            resample=Image.Resampling.BICUBIC
        )


class TransformationRotate90(TransformationRotate):
    arguments = ()
    degrees = 90
    label = _(message='Rotate 90 degrees')
    name = 'rotate90'

    def __init__(self, **kwargs):
        super().__init__()
        self.kwargs['degrees'] = 90


class TransformationRotate180(TransformationRotate):
    arguments = ()
    degrees = 180
    label = _(message='Rotate 180 degrees')
    name = 'rotate180'

    def __init__(self, **kwargs):
        super().__init__()
        self.kwargs['degrees'] = 180


class TransformationRotate270(TransformationRotate):
    arguments = ()
    degrees = 270
    label = _(message='Rotate 270 degrees')
    name = 'rotate270'

    def __init__(self, **kwargs):
        super().__init__()
        self.kwargs['degrees'] = 270


class TransformationUnsharpMask(BaseTransformation):
    arguments = ('radius', 'percent', 'threshold')
    label = _(message='Unsharp masking')
    name = 'unsharpmask'

    class Form(forms.Form):
        radius = form_fields.IntegerField(
            initial=2, help_text=_(message='The blur radius in pixels.'),
            label=_(message='Radius'), required=True
        )
        percent = form_fields.FloatField(
            initial=150, help_text=_(message='Unsharp strength in percent.'),
            label=_(message='Percent'), required=True
        )
        threshold = form_fields.IntegerField(
            initial=3, help_text=_(
                message='Minimum brightness change that will be sharpened.'
            ), label=_(message='Tthreshold'), required=True
        )

    def execute_on(self, *args, **kwargs):
        super().execute_on(*args, **kwargs)

        return self.image.filter(
            ImageFilter.UnsharpMask(
                radius=self.radius, percent=self.percent,
                threshold=self.threshold
            )
        )


class TransformationZoom(BaseTransformation):
    arguments = ('percent',)
    label = _(message='Zoom')
    name = 'zoom'

    class Form(forms.Form):
        percent = form_fields.FloatField(
            help_text=_(message='Zoom level in percent.'),
            label=_(message='Percent'), required=True
        )

    def execute_on(self, *args, **kwargs):
        super().execute_on(*args, **kwargs)

        percent = float(self.percent or '100')

        if percent == 100:
            return self.image

        decimal_value = percent / 100

        width = int(self.image.size[0] * decimal_value)
        if width < 1:
            width = 1

        height = int(self.image.size[1] * decimal_value)
        if height < 1:
            height = 1

        return self.image.resize(
            size=(width, height), resample=Image.Resampling.LANCZOS
        )



BaseTransformation.register(
    layer=layer_decorations, transformation=TransformationAssetPaste
)
BaseTransformation.register(
    layer=layer_decorations, transformation=TransformationAssetPastePercent
)
BaseTransformation.register(
    layer=layer_decorations, transformation=TransformationAssetWatermark
)
BaseTransformation.register(
    layer=layer_decorations,
    transformation=TransformationDrawRectangle
)
BaseTransformation.register(
    layer=layer_decorations,
    transformation=TransformationDrawRectanglePercent
)
BaseTransformation.register(
    layer=layer_decorations, transformation=TransformationDrawText
)
BaseTransformation.register(
    layer=layer_decorations, transformation=TransformationDrawTextPercent
)
BaseTransformation.register(
    layer=layer_decorations, transformation=TransformationQRCodePercent
)


BaseTransformation.register(
    layer=layer_saved_transformations, transformation=TransformationCrop
)
BaseTransformation.register(
    layer=layer_saved_transformations, transformation=TransformationFlip
)
BaseTransformation.register(
    layer=layer_saved_transformations,
    transformation=TransformationGaussianBlur
)
BaseTransformation.register(
    layer=layer_saved_transformations, transformation=TransformationLineArt
)
BaseTransformation.register(
    layer=layer_saved_transformations, transformation=TransformationMirror
)
BaseTransformation.register(
    layer=layer_saved_transformations, transformation=TransformationResize
)
BaseTransformation.register(
    layer=layer_saved_transformations, transformation=TransformationRotate
)
BaseTransformation.register(
    layer=layer_saved_transformations, transformation=TransformationRotate90
)
BaseTransformation.register(
    layer=layer_saved_transformations, transformation=TransformationRotate180
)
BaseTransformation.register(
    layer=layer_saved_transformations, transformation=TransformationRotate270
)
BaseTransformation.register(
    layer=layer_saved_transformations,
    transformation=TransformationUnsharpMask
)
BaseTransformation.register(
    layer=layer_saved_transformations, transformation=TransformationZoom
)
