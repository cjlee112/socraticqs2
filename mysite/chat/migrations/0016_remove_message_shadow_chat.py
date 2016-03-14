# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0015_auto_20160314_0834'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='shadow_chat',
        ),
    ]
