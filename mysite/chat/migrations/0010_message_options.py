# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0009_message_response_to_check'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='options',
            field=models.CharField(max_length=24, null=True, choices=[(b'different', b'Different'), (b'close', b'Close'), (b'correct', b'Essentially the same')]),
            preserve_default=True,
        ),
    ]
