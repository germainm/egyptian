import re
DEFAULT_TEMPLATING_TAGS_DANGEROUS_ALLOW_LIST = 'method'

REGULAR_AJAX_TEMPLATE_HASH_EXCLUDE_PAIR = re.compile(pattern=r'<!--\s*mayan-templating-hash-exclude-start\s*-->.*?<!--\s*mayan-templating-hash-exclude-end\s*-->', flags=re.DOTALL)
