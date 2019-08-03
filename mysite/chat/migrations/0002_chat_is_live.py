from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='is_live',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
