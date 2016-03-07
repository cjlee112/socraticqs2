# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0011_auto_20160304_0645'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='fsm_state',
            field=models.OneToOneField(null=True, to='fsm.FSMState'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='message',
            name='contenttype',
            field=models.CharField(default=b'NoneType', max_length=16, null=True, choices=[(b'NoneType', b'NoneType'), (b'divider', b'divider'), (b'response', b'response'), (b'unitlesson', b'unitlesson'), (b'uniterror', b'uniterror')]),
            preserve_default=True,
        ),
    ]
