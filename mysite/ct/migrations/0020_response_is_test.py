# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0019_auto_20160614_0335'),
    ]

    operations = [
        migrations.AddField(
            model_name='response',
            name='is_test',
            field=models.BooleanField(default=False),
        ),
    ]
