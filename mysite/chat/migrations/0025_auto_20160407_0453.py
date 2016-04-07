# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0024_chatdivider_unitlesson'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatdivider',
            name='unitlesson',
            field=models.ForeignKey(to='ct.UnitLesson', null=True),
            preserve_default=True,
        ),
    ]
