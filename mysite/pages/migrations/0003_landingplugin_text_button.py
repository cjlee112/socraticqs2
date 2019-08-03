from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0002_auto_20151020_2140'),
    ]

    operations = [
        migrations.AddField(
            model_name='landingplugin',
            name='text_button',
            field=models.CharField(max_length=70, null=True, blank=True),
            preserve_default=True,
        ),
    ]
