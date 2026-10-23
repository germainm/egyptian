from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('document_states', '0041_alter_workflowstateaction_label')
    ]

    operations = [
        migrations.AlterField(
            model_name='workflowinstancelogentry',
            name='transition',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='document_states.workflowtransition',
                verbose_name='Transition'
            )
        )
    ]
