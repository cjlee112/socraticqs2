# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0007_auto_20170314_1422'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='last_modify_timestamp',
            field=models.DateTimeField(default=datetime.datetime(2017, 5, 10, 13, 4, 3, 722796, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
    ]
