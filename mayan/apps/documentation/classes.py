from pathlib import Path

from django.apps import apps
from django.conf import settings

from .literals import (
    FEATURE_CATEGORY_LIST, FEATURE_PAGE_FILENAME,
    FEATURE_PAGE_HEADER_LINE_LIST, FEATURE_PAGE_TITLE_OTHER
)


class FeaturePage:
    filename_fragment_body = '_features.txt'
    filename_fragment_footer = '_features_footer.txt'

    @classmethod
    def get_path(cls):
        path_documentation = Path(
            settings.BASE_DIR, '..', 'docs'
        )

        return path_documentation / 'chapters' / FEATURE_PAGE_FILENAME

    @classmethod
    def _get_category_text(cls, body_list, title):
        text_list = [
            '\n', '{}\n'.format(title), '{}\n'.format(
                '=' * len(title)
            ), '\n'
        ]

        for body in body_list:
            text_list.append(body)

            if not body.endswith('\n'):
                text_list.append('\n')

        return ''.join(text_list)

    @classmethod
    def _get_fragments(cls):
        body_map = {}
        footer_list = []

        for app_config in apps.get_app_configs():
            path_app_documentation = Path(app_config.path, 'docs')
            path_body = path_app_documentation / cls.filename_fragment_body

            try:
                file_object = path_body.open(mode='r')
            except FileNotFoundError:
                continue
            else:
                with file_object:
                    body_map[app_config.label] = file_object.read()

            path_footer = (
                path_app_documentation / cls.filename_fragment_footer
            )

            try:
                file_object = path_footer.open(mode='r')
            except FileNotFoundError:
                """
                Non fatal, just means the app does not provide a features
                footer.
                """
            else:
                with file_object:
                    footer_list.append(
                        file_object.read()
                    )

        return body_map, footer_list

    @classmethod
    def do_write(cls):
        body_map, footer_list = cls._get_fragments()

        text_list = list(FEATURE_PAGE_HEADER_LINE_LIST)
        label_set_categorized = set()

        for title, label_list in FEATURE_CATEGORY_LIST:
            category_body_list = []

            for label in label_list:
                label_set_categorized.add(label)

                body = body_map.get(label)

                if body:
                    category_body_list.append(body)

            if category_body_list:
                text_list.append(
                    cls._get_category_text(
                        body_list=category_body_list, title=title
                    )
                )

        label_list_uncategorized = [
            label for label in sorted(body_map) if label not in label_set_categorized
        ]

        if label_list_uncategorized:
            body_list_uncategorized = [
                body_map[label] for label in label_list_uncategorized
            ]
            text_list.append(
                cls._get_category_text(
                    body_list=body_list_uncategorized,
                    title=FEATURE_PAGE_TITLE_OTHER
                )
            )

        text_list.append('\n')
        text_list.extend(footer_list)

        path = cls.get_path()

        with path.open(mode='w') as file_object:
            file_object.write(
                ''.join(text_list)
            )

        return label_list_uncategorized
