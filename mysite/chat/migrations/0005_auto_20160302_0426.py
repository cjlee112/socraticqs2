# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0016_auto_20150626_0301'),
        ('chat', '0004_auto_20160301_1306'),
    ]

    operations = [
        migrations.AddField(
            model_name='enrollunitcode',
            name='courseUnit',
            field=models.ForeignKey(default=1, to='ct.CourseUnit'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='enrollunitcode',
            unique_together=set([('enrollCode', 'courseUnit')]),
        ),
        migrations.RemoveField(
            model_name='enrollunitcode',
            name='unit',
        ),
    ]
