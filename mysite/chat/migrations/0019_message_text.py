# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0018_auto_20160316_1214'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='text',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
