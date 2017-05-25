# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lti', '0008_auto_20170413_0257'),
    ]

    operations = [
        migrations.AddField(
            model_name='outcomeservice',
            name='lti_consumer',
            field=models.ForeignKey(default=1, to='lti.LtiConsumer'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='gradedlaunch',
            unique_together=set([('outcome_service', 'lis_result_sourcedid', 'user', 'course_id')]),
        ),
    ]
