# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0016_auto_20150626_0301'),
        ('chat', '0008_message_lesson_to_answer'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='response_to_check',
            field=models.ForeignKey(to='ct.Response', null=True),
            preserve_default=True,
        ),
    ]
