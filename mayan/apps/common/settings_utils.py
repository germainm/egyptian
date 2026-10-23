from django.utils.module_loading import import_string


def do_extra_settings_function_apply(
    installed_apps, middleware, dotted_path_string
):
    stripped_entry_list = (
        entry.strip() for entry in dotted_path_string.split(',')
    )
    dotted_path_list = filter(None, stripped_entry_list)

    for dotted_path in dotted_path_list:
        settings_function = import_string(dotted_path=dotted_path)
        installed_apps, middleware = settings_function(
            installed_apps=installed_apps, middleware=middleware
        )

    return (installed_apps, middleware)
