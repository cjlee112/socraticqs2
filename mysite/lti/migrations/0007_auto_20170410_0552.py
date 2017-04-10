# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lti', '0006_auto_20170329_0215'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='ltiuser',
            unique_together=set([('user_id', 'lti_consumer')]),
        ),
        migrations.RemoveField(
            model_name='ltiuser',
            name='context_id',
        ),
    ]
