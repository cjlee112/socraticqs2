# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0025_auto_20160407_0453'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='kind',
            field=models.CharField(max_length=32, null=True, choices=[(b'base', b'base'), (b'orct', b'orct'), (b'answer', b'answer'), (b'errmod', b'errmod'), (b'chatdivider', b'chatdivider'), (b'uniterror', b'uniterror'), (b'response', b'response'), (b'message', b'message'), (b'button', b'button')]),
            preserve_default=True,
        ),
    ]
