import re

from mayan.apps.smart_settings.namespace_migrations import (
    SettingNamespaceMigration
)

from .literals import (
    REGULAR_EXPRESSION_PERCENT_INTERPOLATION,
    REPLACEMENT_PERCENT_INTERPOLATION
)


class MailerSettingMigration(SettingNamespaceMigration):
    @staticmethod
    def get_value_percent_interpolation_removed(value):
        if not isinstance(value, str):
            return value

        def replacement_function(match):
            return REPLACEMENT_PERCENT_INTERPOLATION[
                match.group(0)
            ]

        return re.sub(
            pattern=REGULAR_EXPRESSION_PERCENT_INTERPOLATION,
            repl=replacement_function, string=value
        )

    def mailer_document_body_template_0001(self, value):
        return MailerSettingMigration.get_value_percent_interpolation_removed(
            value=value
        )

    def mailer_link_body_template_0001(self, value):
        return MailerSettingMigration.get_value_percent_interpolation_removed(
            value=value
        )
