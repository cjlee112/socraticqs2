from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0019_auto_20160614_0335'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='liked',
            options={'verbose_name_plural': 'Likes'},
        ),
    ]
