from django.db import models, migrations
import djangocms_text_ckeditor.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0027_interestedplugin_bg_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='interestedform',
            name='when_join',
            field=models.TextField(blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interestedplugin',
            name='description_field',
            field=djangocms_text_ckeditor.fields.HTMLField(default='Your Availability: Please provide several day/times that you are available in January for a2-hour kick-off meeting (video conference).'),
            preserve_default=True,
        ),
    ]
