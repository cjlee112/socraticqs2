# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0025_auto_20180402_0432'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lesson',
            name='sub_kind',
            field=models.CharField(blank=True, max_length=50, null=True, choices=[(b'choices', b'Multiple Choices Question'), (b'numbers', b'Numbers'), (b'canvas', b'Canvas')]),
        ),
        migrations.AlterField(
            model_name='response',
            name='sub_kind',
            field=models.CharField(blank=True, max_length=10, null=True, choices=[(b'choices', b'Multiple Choices response'), (b'numbers', b'Numbers response'), (b'canvas', b'Canvas response')]),
        ),
    ]
