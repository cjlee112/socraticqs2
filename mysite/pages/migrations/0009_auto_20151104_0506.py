from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0012_auto_20150607_2207'),
        ('pages', '0008_listplugin'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shortaboutplugin',
            name='cmsplugin_ptr',
        ),
        migrations.DeleteModel(
            name='ShortAboutPlugin',
        ),
        migrations.RemoveField(
            model_name='activelearningratesplugin',
            name='image',
        ),
        migrations.RemoveField(
            model_name='bannerplugin',
            name='background_image',
        ),
        migrations.AddField(
            model_name='bannerplugin',
            name='sponsors_text',
            field=models.CharField(max_length=70, blank=True),
            preserve_default=True,
        ),
    ]
