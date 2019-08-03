from django.db import models, migrations
import djangocms_text_ckeditor.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0025_auto_20151116_0636'),
    ]

    operations = [
        migrations.AddField(
            model_name='benefitsplugin',
            name='description',
            field=djangocms_text_ckeditor.fields.HTMLField(blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='slideshareitemplugin',
            name='title',
            field=models.CharField(max_length=200, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='workshopdescriptionplugin',
            name='description',
            field=djangocms_text_ckeditor.fields.HTMLField(blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='detailsvideoplugin',
            name='description',
            field=models.CharField(max_length=200, blank=True),
            preserve_default=True,
        ),
    ]
