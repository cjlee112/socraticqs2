# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0016_auto_20150626_0301'),
        ('chat', '0007_auto_20160303_0231'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='lesson_to_answer',
            field=models.ForeignKey(to='ct.UnitLesson', null=True),
            preserve_default=True,
        ),
    ]
