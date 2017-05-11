# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0008_chat_last_modify_timestamp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='last_modify_timestamp',
            field=models.DateTimeField(null=True),
        ),
    ]
