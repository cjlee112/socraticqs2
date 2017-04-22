# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('psa', '0004_customcode'),
    ]

    operations = [
        migrations.AddField(
            model_name='customcode',
            name='force_update',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='secondaryemail',
            name='email',
            field=models.EmailField(max_length=254, verbose_name=b'Secondary Email'),
        ),
    ]
