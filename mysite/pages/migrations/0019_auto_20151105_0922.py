from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0018_interestedform_interestedplugin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='detailsplugin',
            name='quote_small',
            field=models.CharField(max_length=70, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='detailsplugin',
            name='quote_text',
            field=models.CharField(max_length=70, blank=True),
            preserve_default=True,
        ),
    ]
