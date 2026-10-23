from django.utils.translation import gettext_lazy as _

from mayan.apps.sources.source_backend_actions.interface_arguments import (
    SourceBackendActionInterfaceArgument
)

from ..source_backends.literals import (
    SOURCE_UNCOMPRESS_API_CHOICES, SOURCE_UNCOMPRESS_CHOICE_NEVER
)

argument_expand = SourceBackendActionInterfaceArgument(
    default=False, help_text=_(
        message='Deprecated in favor of `expand_mode`. When true the '
        'uploaded file is expanded and its contained files are processed as '
        'individual documents; a file that expands to nothing is rejected. '
        'Ignored when `expand_mode` is also provided.'
    ), required=False
)

argument_expand_mode = SourceBackendActionInterfaceArgument(
    choices=SOURCE_UNCOMPRESS_API_CHOICES, default=None, help_text=_(
        message='How to expand a compressed or container file into '
        'individual documents. When provided, this overrides the `expand` '
        'boolean. See `choices` for the accepted values.'
    ), required=False
)

argument_uncompress = SourceBackendActionInterfaceArgument(
    default=SOURCE_UNCOMPRESS_CHOICE_NEVER, hidden=True, help_text=_(
        message='Internal resolved decompression mode.'
    ), required=False
)
