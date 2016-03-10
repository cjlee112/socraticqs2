# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0013_auto_20160307_0738'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='type',
            field=models.CharField(default=b'default', max_length=16, choices=[(b'default', b'default'), (b'user', b'user'), (b'breakpoint', b'breakpoint')]),
            preserve_default=True,
        ),
    ]
