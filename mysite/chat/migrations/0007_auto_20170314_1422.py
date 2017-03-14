# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0006_auto_20170117_0513'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatdivider',
            name='text',
            field=models.CharField(max_length=200),
        ),
    ]
