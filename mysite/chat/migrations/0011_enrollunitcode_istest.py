# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0010_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='enrollunitcode',
            name='isTest',
            field=models.BooleanField(default=False),
        ),
    ]
