# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2019-07-19 12:46
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ctms', '0005_bestpractices2'),
    ]

    operations = [
        migrations.AddField(
            model_name='bestpractices',
            name='pdf',
            field=models.FileField(blank=True, null=True, upload_to=b'best_practices/', validators=[django.core.validators.FileExtensionValidator([b'pdf'])]),
        ),
    ]
