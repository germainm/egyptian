from django.db import migrations, models

import mayan.apps.common.validators


class Migration(migrations.Migration):
    dependencies = [
        ('documents', '0001_initial')
    ]
    initial = True

    operations = [
        migrations.CreateModel(
            fields=[
                (
                    'id', models.AutoField(
                        auto_created=True, primary_key=True, serialize=False,
                        verbose_name='ID'
                    )
                ), (
                    'backend_path', models.CharField(
                        help_text='The dotted Python path to the backend '
                        'class.', max_length=128, verbose_name='Backend path'
                    )
                ), (
                    'backend_data', models.TextField(
                        blank=True, help_text='JSON encoded data for the '
                        'backend class.', verbose_name='Backend data'
                    )
                ), (
                    'label', models.CharField(
                        help_text='Short description of this sequence.',
                        max_length=128, unique=True, verbose_name='Label'
                    )
                ), (
                    'internal_name', models.CharField(
                        db_index=True, help_text='This value will be used '
                        'by other apps to reference this sequence. Can only '
                        'contain letters, numbers, and underscores.',
                        max_length=255, unique=True, validators=[
                            mayan.apps.common.validators.validate_internal_name
                        ], verbose_name='Internal name'
                    )
                ), (
                    'position', models.BigIntegerField(
                        db_index=True, default=0, help_text='Zero based '
                        'counter of how many values have been consumed. Set '
                        'this to continue the numbering of a system being '
                        'replaced.', verbose_name='Position'
                    )
                ), (
                    'on_limit', models.CharField(
                        choices=[
                            ('raise', 'Raise an error and consume nothing'),
                            ('wrap', 'Wrap around to the first position')
                        ], default='raise', help_text='What to do when the '
                        'sequence reaches the last position its backend is '
                        'able to represent.', max_length=16,
                        verbose_name='On limit'
                    )
                ), (
                    'document_types', models.ManyToManyField(
                        blank=True, help_text='Document types that are '
                        'allowed to use this sequence. Associating more '
                        'than one document type is supported and means '
                        'those document types draw from the same pool of '
                        'values.', related_name='sequences',
                        to='documents.documenttype',
                        verbose_name='Document types'
                    )
                ), (
                    'value_is_unique', models.BooleanField(
                        default=True, editable=False, help_text='Whether '
                        'a value of this sequence identifies a single '
                        'position. Recorded when the sequence is saved and '
                        'not entered by hand.', null=True,
                        verbose_name='Values are unique'
                    )
                )
            ],
            name='Sequence',
            options={
                'ordering': ('label',),
                'verbose_name': 'Sequence',
                'verbose_name_plural': 'Sequences'
            }
        )
    ]
