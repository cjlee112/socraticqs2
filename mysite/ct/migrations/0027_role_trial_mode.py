# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2018-08-10 15:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0026_course_trial'),
    ]

    operations = [
        migrations.AddField(
            model_name='role',
            name='trial_mode',
            field=models.NullBooleanField(),
        ),
    ]
