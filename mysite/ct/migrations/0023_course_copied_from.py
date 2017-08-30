# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0022_auto_20170527_1519'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='copied_from',
            field=models.ForeignKey(blank=True, to='ct.Course', null=True),
        ),
    ]
