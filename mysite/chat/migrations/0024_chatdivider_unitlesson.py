# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0016_auto_20150626_0301'),
        ('chat', '0023_message_student_error'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatdivider',
            name='unitlesson',
            field=models.ForeignKey(default=1, to='ct.UnitLesson'),
            preserve_default=False,
        ),
    ]
