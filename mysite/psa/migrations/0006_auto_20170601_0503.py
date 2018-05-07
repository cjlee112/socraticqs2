# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('psa', '0005_auto_20170206_0348'),
    ]

    operations = [
        migrations.AddField(
            model_name='customcode',
            name='first_name',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customcode',
            name='institution',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customcode',
            name='last_name',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customcode',
            name='password',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
