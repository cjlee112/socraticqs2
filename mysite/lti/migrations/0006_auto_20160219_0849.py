# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lti', '0005_lticonsumer'),
    ]

    operations = [
        migrations.AddField(
            model_name='ltiuser',
            name='lti_consumer',
            field=models.ForeignKey(to='lti.LtiConsumer', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='ltiuser',
            unique_together=set([('user_id', 'lti_consumer')]),
        ),
        migrations.RemoveField(
            model_name='ltiuser',
            name='context_id',
        ),
        migrations.RemoveField(
            model_name='ltiuser',
            name='consumer',
        ),
    ]
