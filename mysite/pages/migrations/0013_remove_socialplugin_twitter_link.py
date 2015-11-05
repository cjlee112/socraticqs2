# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0012_footerplugin_socialplugin'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='socialplugin',
            name='twitter_link',
        ),
    ]
