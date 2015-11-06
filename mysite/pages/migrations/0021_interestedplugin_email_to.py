# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0020_auto_20151106_0251'),
    ]

    operations = [
        migrations.AddField(
            model_name='interestedplugin',
            name='email_to',
            field=models.EmailField(default=b'cmathews@elancecloud.com', max_length=75),
            preserve_default=True,
        ),
    ]
