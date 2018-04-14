# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0025_auto_20180402_0432'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='enable_auto_grading',
            field=models.BooleanField(default=False),
        ),
    ]
