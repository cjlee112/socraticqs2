from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0016_auto_20150626_0301'),
    ]

    operations = [
        migrations.AddField(
            model_name='unit',
            name='description',
            field=models.TextField(blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='unit',
            name='img_url',
            field=models.URLField(blank=True),
            preserve_default=True,
        ),
    ]
