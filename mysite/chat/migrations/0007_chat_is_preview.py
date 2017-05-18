# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0006_auto_20170117_0513'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='is_preview',
            field=models.BooleanField(default=False),
        ),
    ]
