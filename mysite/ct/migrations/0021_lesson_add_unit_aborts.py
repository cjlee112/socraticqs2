# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0020_auto_20170412_0258'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='add_unit_aborts',
            field=models.NullBooleanField(default=False),
        ),
    ]
