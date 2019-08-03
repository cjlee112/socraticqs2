from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0024_auto_20180512_1527'),
    ]

    operations = [
        migrations.AddField(
            model_name='response',
            name='is_preview',
            field=models.BooleanField(default=False),
        ),
    ]
