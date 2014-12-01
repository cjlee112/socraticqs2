# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0005_unitstatus'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseunit',
            name='releaseTime',
            field=models.DateTimeField(null=True, verbose_name=b'time released'),
            preserve_default=True,
        ),
    ]
