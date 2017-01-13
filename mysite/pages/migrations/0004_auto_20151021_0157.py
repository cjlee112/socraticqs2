# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0003_landingplugin_text_button'),
    ]

    operations = [
        migrations.AlterField(
            model_name='landingplugin',
            name='block_color',
            field=models.CharField(default=b'bg-primary', max_length=20, choices=[(b'bg-primary', b'blue'), (b'bg-danger', b'red'), (b'bg-success', b'green'), (b'bg-info', b'light-blue'), (b'bg-warning', b'yellow')]),
            preserve_default=True,
        ),
    ]
