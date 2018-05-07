# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0026_lesson_enable_auto_grading'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lesson',
            name='number_precision',
        ),
        migrations.AddField(
            model_name='lesson',
            name='number_value',
            field=models.FloatField(default=0),
        ),
    ]
