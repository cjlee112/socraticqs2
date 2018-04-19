# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0026_auto_20180418_0314'),
    ]

    operations = [
        migrations.AddField(
            model_name='response',
            name='attachment',
            field=models.FileField(null=True, upload_to=b'answers', blank=True),
        ),
    ]
