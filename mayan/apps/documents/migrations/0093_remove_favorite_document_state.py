from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('document_favorites', '0001_initial'),
        ('documents', '0092_alter_favoritedocument_unique_together')
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name='FavoriteDocumentProxy'),
                migrations.DeleteModel(name='FavoriteDocument')
            ]
        )
    ]
