# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lti', '0006_auto_20160219_0849'),
    ]

    operations = [
        migrations.AddField(
            model_name='lticonsumer',
            name='expiration_date',
            field=models.DateField(null=True, verbose_name=b'Consumer Key expiration date', blank=True),
            preserve_default=True,
        ),
    ]
