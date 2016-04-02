# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0016_auto_20150626_0301'),
        ('chat', '0022_auto_20160323_0833'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='student_error',
            field=models.ForeignKey(to='ct.StudentError', null=True),
            preserve_default=True,
        ),
    ]
