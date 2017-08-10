# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0009_chat_progress'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='chat',
            options={'ordering': ['-last_modify_timestamp']},
        ),
    ]
