# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0007_auto_20150112_1604'),
    ]

    operations = [
        migrations.RenameField(
            model_name='fsmstate',
            old_name='isModal',
            new_name='hideTabs',
        ),
        migrations.AddField(
            model_name='fsm',
            name='hideLinks',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsm',
            name='hideNav',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsm',
            name='hideTabs',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsmstate',
            name='hideLinks',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsmstate',
            name='hideNav',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsmstate',
            name='title',
            field=models.CharField(default='Boo!', max_length=200),
            preserve_default=False,
        ),
    ]
