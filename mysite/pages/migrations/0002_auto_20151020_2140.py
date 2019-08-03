from django.db import models, migrations
import djangocms_text_ckeditor.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='landingplugin',
            old_name='button',
            new_name='link_button',
        ),
        migrations.AddField(
            model_name='landingplugin',
            name='block_color',
            field=models.CharField(default='bg-primary', max_length=20, choices=[('blue', 'bg-primary'), ('red', 'bg-danger'), ('green', 'bg-success'), ('light-blue', 'bg-info'), ('yellow', 'bg-warning')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='landingplugin',
            name='description',
            field=djangocms_text_ckeditor.fields.HTMLField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='landingplugin',
            name='list_description',
            field=djangocms_text_ckeditor.fields.HTMLField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
