# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_auto_20160302_0426'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='enroll_code',
            field=models.ForeignKey(to='chat.EnrollUnitCode', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='message',
            name='input_type',
            field=models.CharField(max_length=16, null=True, choices=[(b'text', b'text'), (b'options', b'options'), (b'custom', b'custom')]),
            preserve_default=True,
        ),
    ]
