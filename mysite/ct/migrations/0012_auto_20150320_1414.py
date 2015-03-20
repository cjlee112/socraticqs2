# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0011_auto_20150129_1209'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fsmedge',
            name='funcName',
        ),
        migrations.AddField(
            model_name='fsmedge',
            name='showOption',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
