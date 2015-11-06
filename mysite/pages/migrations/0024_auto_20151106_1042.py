# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djangocms_text_ckeditor.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0023_auto_20151106_1031'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interestedplugin',
            name='description_field',
            field=djangocms_text_ckeditor.fields.HTMLField(default=b'We plan to host hackathons between ? and ?. Please tell us more about your availability below. Our hackathons are split into 3 meetings that are about 2 hours long.'),
            preserve_default=True,
        ),
    ]
