# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0006_auto_20170117_0513'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='last_modify_timestamp',
            field=models.DateTimeField(default=datetime.datetime(2017, 1, 27, 18, 2, 3, 769600, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
    ]
