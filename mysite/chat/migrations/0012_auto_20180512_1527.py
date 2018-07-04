# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0011_auto_20170614_0341'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='is_preview',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='chat',
            name='is_test',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='enrollunitcode',
            name='isPreview',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='enrollunitcode',
            name='isTest',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='chat',
            name='progress',
            field=models.IntegerField(default=0, null=True, blank=True),
        ),
    ]
