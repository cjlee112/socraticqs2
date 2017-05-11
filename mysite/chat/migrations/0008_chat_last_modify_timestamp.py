# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0007_auto_20170314_1422'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='last_modify_timestamp',
            field=models.DateTimeField(null=True),
        ),
    ]
