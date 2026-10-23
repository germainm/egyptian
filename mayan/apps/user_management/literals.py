from django.utils.translation import gettext_lazy as _

FIELDSETS_ALL = (
    (
        _(message='Account'), {
            'fields': ('username', 'email')
        }
    ), (
        _(message='Personal'), {
            'fields': ('first_name', 'last_name')
        },
    ), (
        _(message='Attributes'), {
            'fields': ('is_active',)
        },
    )
)
FIELDSETS_USER = (
    (
        _(message='Personal'), {
            'fields': ('first_name', 'last_name')
        },
    ),
)

FIELDS_ALL = ('username', 'first_name', 'last_name', 'email', 'is_active')
FIELDS_USER = ('first_name', 'last_name')
