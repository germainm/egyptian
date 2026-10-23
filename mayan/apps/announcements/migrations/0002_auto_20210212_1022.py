from django.db import migrations


def code_copy_messages(apps, schema_editor):
    AccessControlList = apps.get_model(
        app_label='acls', model_name='AccessControlList'
    )
    Action = apps.get_model(
        app_label='actstream', model_name='Action'
    )
    Announcement = apps.get_model(
        app_label='announcements', model_name='Announcement'
    )
    ContentType = apps.get_model(
        app_label='contenttypes', model_name='ContentType'
    )
    Message = apps.get_model(app_label='motd', model_name='Message')
    StoredEventType = apps.get_model(
        app_label='events', model_name='StoredEventType'
    )
    StoredPermission = apps.get_model(
        app_label='permissions', model_name='StoredPermission'
    )

    alias = schema_editor.connection.alias

    announcement_content_type = ContentType.objects.get_for_model(
        model=Announcement
    )
    message_content_type = ContentType.objects.get_for_model(model=Message)

    for message in Message.objects.using(alias=alias).all():
        announcement = Announcement.objects.using(alias=alias).create(
            enabled=message.enabled, label=message.label,
            text=message.message, start_datetime=message.start_datetime,
            end_datetime=message.end_datetime
        )

        queryset_message_acls = AccessControlList.objects.using(
            alias=alias
        ).filter(
            content_type=message_content_type, object_id=message.pk
        )

        for message_acl in queryset_message_acls:
            message_acl._event_ignore = True
            message_acl.content_type = announcement_content_type
            message_acl.object_id = announcement.pk
            message_acl.save(using=alias)

        queryset_message_action = Action.objects.using(
            alias=alias
        ).filter(
            target_content_type=message_content_type,
            target_object_id=message.pk
        )

        for message_action in queryset_message_action:
            message_action.target_content_type = announcement_content_type
            message_action.target_object_id = announcement.pk
            message_action.save(using=alias)

        message.delete(using=alias)

    queryset_stored_event = StoredEventType.objects.using(
        alias=alias
    ).filter(name__startswith='motd')

    for stored_event_type in queryset_stored_event:
        stored_event_type.name = stored_event_type.name.replace(
            'motd', 'announcements'
        ).replace('message', 'announcement')
        stored_event_type.save(using=alias)

    queryset_stored_permissions = StoredPermission.objects.using(
        alias=alias
    ).filter(namespace='motd')

    for stored_permission in queryset_stored_permissions:
        stored_permission.namespace = stored_permission.namespace.replace(
            'motd', 'announcements'
        )
        stored_permission.name = stored_permission.name.replace(
            'message', 'announcement'
        )
        stored_permission.save(using=alias)


def code_copy_messages_reverse(apps, schema_editor):
    AccessControlList = apps.get_model(
        app_label='acls', model_name='AccessControlList'
    )
    Action = apps.get_model(
        app_label='actstream', model_name='Action'
    )
    Announcement = apps.get_model(
        app_label='announcements', model_name='Announcement'
    )
    ContentType = apps.get_model(
        app_label='contenttypes', model_name='ContentType'
    )
    Message = apps.get_model(app_label='motd', model_name='Message')
    StoredEventType = apps.get_model(
        app_label='events', model_name='StoredEventType'
    )
    StoredPermission = apps.get_model(
        app_label='permissions', model_name='StoredPermission'
    )

    alias = schema_editor.connection.alias

    announcement_content_type = ContentType.objects.get_for_model(
        model=Announcement
    )

    message_content_type = ContentType.objects.get_for_model(model=Message)

    for announcement in Announcement.objects.using(alias=alias).all():
        message = Message.objects.using(alias=alias).create(
            enabled=announcement.enabled, label=announcement.label,
            message=announcement.text,
            start_datetime=announcement.start_datetime,
            end_datetime=announcement.end_datetime
        )

        queryset_announcement_acls = AccessControlList.objects.using(
            alias=alias
        ).filter(
            content_type=announcement_content_type, object_id=announcement.pk
        )

        for announcement_acl in queryset_announcement_acls:
            announcement_acl._event_ignore = True
            announcement_acl.content_type = message_content_type
            announcement_acl.object_id = message.pk
            announcement_acl.save(using=alias)

        queryset_announcement_action = Action.objects.using(
            alias=alias
        ).filter(
            target_content_type=announcement_content_type,
            target_object_id=announcement.pk
        )

        for announcement_action in queryset_announcement_action:
            announcement_action.target_content_type = message_content_type
            announcement_action.target_object_id = message.pk
            announcement_action.save(using=alias)

        announcement.delete(using=alias)

    queryset_stored_event = StoredEventType.objects.using(
        alias=alias
    ).filter(name__startswith='announcements')

    for stored_event_type in queryset_stored_event:
        stored_event_type.name = stored_event_type.name.replace(
            'announcements', 'motd'
        ).replace('announcement', 'message')
        stored_event_type.save(using=alias)

    queryset_stored_permissions = StoredPermission.objects.using(
        alias=alias
    ).filter(namespace='announcements')

    for stored_permission in queryset_stored_permissions:
        stored_permission.namespace = stored_permission.namespace.replace(
            'announcements', 'motd'
        )
        stored_permission.name = stored_permission.name.replace(
            'announcement', 'message'
        )
        stored_permission.save(using=alias)


class Migration(migrations.Migration):
    dependencies = [
        ('acls', '0004_auto_20210130_0322'),
        ('announcements', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('events', '0008_auto_20180315_0029'),
        ('permissions', '0004_auto_20191213_0044')
    ]

    operations = [
        migrations.RunPython(
            code=code_copy_messages,
            reverse_code=code_copy_messages_reverse
        )
    ]
