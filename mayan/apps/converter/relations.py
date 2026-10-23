from furl import furl

from mayan.apps.rest_api.relations import MultiKwargHyperlinkedIdentityField

from .exceptions import AppImageError


class ImageURLField(MultiKwargHyperlinkedIdentityField):
    def get_url(self, obj, view_name, request, format):
        result = super().get_url(
            obj=obj, view_name=view_name, request=request, format=format
        )

        if not result:
            return result

        try:
            api_image_url = obj.get_api_image_url()
        except AppImageError:
            """
            The transformations of the object cannot be resolved. The URL
            is returned without arguments. Requesting it produces the
            error image for the condition, which is the same result as
            before.
            """
            return result

        final_url = furl(url=result)

        final_url.args.update(
            furl(url=api_image_url).args
        )

        return final_url.tostr()
