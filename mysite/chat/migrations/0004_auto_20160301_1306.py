# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_auto_20160301_1229'),
    ]

    operations = [
        migrations.RenameField(
            model_name='chat',
            old_name='next_step',
            new_name='next_point',
        ),
        migrations.AlterField(
            model_name='message',
            name='contenttype',
            field=models.CharField(default=b'NoneType', max_length=16, null=True, choices=[(b'NoneType', b'NoneType'), (b'divider', b'divider'), (b'response', b'response'), (b'unitlesson', b'unitlesson')]),
            preserve_default=True,
        ),
    ]
