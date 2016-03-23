# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0019_message_text'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='message',
            options={'ordering': ['timestamp']},
        ),
        migrations.AddField(
            model_name='message',
            name='userMessage',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='message',
            name='kind',
            field=models.CharField(max_length=32, null=True, choices=[(b'base', b'base'), (b'orct', b'orct'), (b'answer', b'answer'), (b'errmod', b'errmod'), (b'chatdivider', b'chatdivider'), (b'uniterror', b'uniterror'), (b'response', b'response'), (b'message', b'message')]),
            preserve_default=True,
        ),
    ]
