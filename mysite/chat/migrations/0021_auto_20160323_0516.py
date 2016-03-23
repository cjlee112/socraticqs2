# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0020_auto_20160323_0442'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='type',
            field=models.CharField(default=b'message', max_length=16, choices=[(b'message', b'message'), (b'user', b'user'), (b'breakpoint', b'breakpoint')]),
            preserve_default=True,
        ),
    ]
