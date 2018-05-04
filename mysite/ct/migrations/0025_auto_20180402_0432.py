# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0024_auto_20170719_0551'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='number_max_value',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='lesson',
            name='number_min_value',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='lesson',
            name='number_precision',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='lesson',
            name='sub_kind',
            field=models.CharField(blank=True, max_length=50, null=True, choices=[(b'choices', b'Multiple Choices Question'), (b'numbers', b'Numbers')]),
        ),
        migrations.AlterField(
            model_name='response',
            name='sub_kind',
            field=models.CharField(blank=True, max_length=10, null=True, choices=[(b'choices', b'Multiple Choices response'), (b'numbers', b'Numbers response')]),
        ),
    ]
