# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-11-16 14:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0013_chat_is_trial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='kind',
            field=models.CharField(choices=[(b'base', b'base'), (b'orct', b'orct'), (b'answer', b'answer'), (b'errmod', b'errmod'), ('chatdivider', 'chatdivider'), ('uniterror', 'uniterror'), ('response', 'response'), ('message', 'message'), ('button', 'button'), ('abort', 'abort')], max_length=32, null=True),
        ),
    ]