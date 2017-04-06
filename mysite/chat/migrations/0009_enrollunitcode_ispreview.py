# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0008_chat_is_test'),
    ]

    operations = [
        migrations.AddField(
            model_name='enrollunitcode',
            name='isPreview',
            field=models.BooleanField(default=False),
        ),
    ]
