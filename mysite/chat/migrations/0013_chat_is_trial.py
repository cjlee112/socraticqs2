from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0012_auto_20180512_1527'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='is_trial',
            field=models.BooleanField(default=False),
        ),
    ]
