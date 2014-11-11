# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0002_auto_20141110_1820'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conceptlink',
            name='relationship',
            field=models.CharField(default=b'defines', max_length=10, choices=[(b'is', b'Represents (unique ID for)'), (b'defines', b'Defines'), (b'informal', b'Intuitive statement of'), (b'formaldef', b'Formal definition for'), (b'tests', b'Tests understanding of'), (b'derives', b'Derives'), (b'proves', b'Proves'), (b'assumes', b'Assumes'), (b'motiv', b'Motivates'), (b'illust', b'Illustrates'), (b'intro', b'Introduces'), (b'comment', b'Comments on'), (b'warns', b'Warning about')]),
        ),
    ]
