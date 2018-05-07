# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0012_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='progress',
            field=models.IntegerField(default=0, null=True, blank=True),
        ),
    ]
