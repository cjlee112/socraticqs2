from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0017_auto_20160411_0446'),
    ]

    operations = [
        migrations.AddField(
            model_name='unit',
            name='small_img_url',
            field=models.URLField(blank=True),
            preserve_default=True,
        ),
    ]
