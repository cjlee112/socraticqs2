from django.db import models, migrations
import djangocms_text_ckeditor.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0021_auto_20151106_0444'),
    ]

    operations = [
        migrations.AddField(
            model_name='activelearningratesplugin',
            name='fig_alt',
            field=models.CharField(max_length=70, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activelearningratesplugin',
            name='fig_caption',
            field=models.CharField(max_length=70, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activelearningratesplugin',
            name='list_text',
            field=djangocms_text_ckeditor.fields.HTMLField(default=''),
            preserve_default=False,
        ),
    ]
