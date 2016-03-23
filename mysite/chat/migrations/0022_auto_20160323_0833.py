# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0021_auto_20160323_0516'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='input_type',
            field=models.CharField(default=b'options', max_length=16, null=True, choices=[(b'text', b'text'), (b'options', b'options'), (b'custom', b'custom')]),
            preserve_default=True,
        ),
    ]
