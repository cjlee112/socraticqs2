# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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
            field=models.CharField(default=b'bg-primary', max_length=20, choices=[(b'blue', b'bg-primary'), (b'red', b'bg-danger'), (b'green', b'bg-success'), (b'light-blue', b'bg-info'), (b'yellow', b'bg-warning')]),
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
