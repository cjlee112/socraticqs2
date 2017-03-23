# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0007_chat_is_preview'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='is_test',
            field=models.BooleanField(default=False),
        ),
    ]
