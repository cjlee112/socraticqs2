# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0022_auto_20151106_1014'),
    ]

    operations = [
        migrations.RenameField(
            model_name='interestedform',
            old_name='description',
            new_name='when_join',
        ),
    ]
