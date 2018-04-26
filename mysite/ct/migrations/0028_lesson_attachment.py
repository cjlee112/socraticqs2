# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0027_response_attachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='attachment',
            field=models.FileField(null=True, upload_to=b'questions', blank=True),
        ),
    ]
