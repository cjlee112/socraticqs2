# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0021_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unit',
            name='title',
            field=models.CharField(help_text=b'Your students will see this, so give your courselet a descriptive name.', max_length=200),
        ),
    ]
