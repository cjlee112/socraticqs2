# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_auto_20161128_0759'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
