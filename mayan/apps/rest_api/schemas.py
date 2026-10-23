from typing import get_type_hints

from drf_spectacular.openapi import AutoSchema as SpectacularAutoSchema
from drf_spectacular.plumbing import build_basic_type, get_override
from drf_spectacular.types import OpenApiTypes


class AutoSchema(SpectacularAutoSchema):
    def _map_response_type_hint(self, method):
        override = get_override(method, 'field')

        try:
            type_hint = get_type_hints(method).get('return')
        except Exception:
            type_hint = None

        if override is None and type_hint is None:
            return build_basic_type(OpenApiTypes.STR)

        return super()._map_response_type_hint(method)
