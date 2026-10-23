FEATURE_CATEGORY_LIST = (
    (
        'Documents and files', (
            'documents', 'converter', 'redactions', 'duplicates',
            'document_downloads', 'document_exports', 'document_favorites'
        )
    ),
    (
        'Capture and sources', (
            'sources', 'mailer', 'mirroring', 'web_links'
        )
    ),
    (
        'Organization and search', (
            'metadata', 'tags', 'cabinets', 'document_indexing', 'linking',
            'dynamic_search', 'sequences'
        )
    ),
    (
        'Processing and intelligence', (
            'ocr', 'document_parsing', 'file_metadata', 'file_metadata_openai',
            'file_metadata_ollama', 'file_metadata_clamav'
        )
    ),
    (
        'Automation and collaboration', (
            'document_states', 'document_comments', 'checkouts', 'events',
            'messaging', 'announcements'
        )
    ),
    (
        'Security and access control', (
            'acls', 'authentication', 'authentication_otp',
            'authentication_oidc', 'authentication_attempts', 'django_gpg',
            'document_signatures', 'signature_captures', 'credentials'
        )
    ),
    (
        'Administration and platform', (
            'common', 'appearance', 'dashboards', 'smart_settings', 'quotas',
            'mayan_statistics', 'storage', 'rest_api', 'templating', 'locales',
            'user_management'
        )
    )
)

FEATURE_PAGE_FILENAME = 'features.txt'

FEATURE_PAGE_HEADER_LINE_LIST = (
    '.. _features:\n\n', '========\n', 'Features\n', '========\n', '\n',
    'Everything Mayan EDMS can do, grouped by what you are trying to '
    'accomplish.\n', '\n'
)

FEATURE_PAGE_TITLE_OTHER = 'Other'
