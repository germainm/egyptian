from mayan.apps.dependencies.classes import (
    JavaScriptDependency, PythonDependency
)
from mayan.apps.dependencies.environments import environment_production

JavaScriptDependency(
    environments=(environment_production,), module=__name__,
    name='signature_pad', replace_list=[
        {
            'filename_pattern': '*.umd.js',
            'content_patterns': [
                {
                    'search': '//# sourceMappingURL=signature_pad.umd.js.map',
                    'replace': '',
                }
            ]
        }
    ], version_string='=4.2.0'
)

