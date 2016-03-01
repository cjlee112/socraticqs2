# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_auto_20160229_0756'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='chat',
            field=models.ForeignKey(to='chat.Chat', null=True),
            preserve_default=True,
        ),
    ]
