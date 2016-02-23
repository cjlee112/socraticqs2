# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import lti.utils


class Migration(migrations.Migration):

    dependencies = [
        ('lti', '0007_lticonsumer_expiration_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lticonsumer',
            name='consumer_key',
            field=models.CharField(default=lti.utils.key_secret_generator, unique=True, max_length=32, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='lticonsumer',
            name='consumer_secret',
            field=models.CharField(default=lti.utils.key_secret_generator, unique=True, max_length=32),
            preserve_default=True,
        ),
    ]
