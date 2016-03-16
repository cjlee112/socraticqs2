# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0016_remove_message_shadow_chat'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='is_additional',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
