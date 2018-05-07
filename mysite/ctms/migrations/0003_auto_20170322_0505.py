# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ct', '0025_auto_20180405_1334'),
        ('accounts', '0002_auto_20160411_1313'),
        ('ctms', '0002_auto_20170317_0936'),
    ]

    operations = [
        # migrations.RemoveField(
        #     model_name='sharedcourse',
        #     name='course',
        # ),
        # migrations.RemoveField(
        #     model_name='sharedcourse',
        #     name='from_user',
        # ),
        # migrations.RemoveField(
        #     model_name='sharedcourse',
        #     name='to_user',
        # ),
        migrations.DeleteModel(
            name='SharedCourse',
        ),
        migrations.AlterUniqueTogether(
            name='invite',
            unique_together=set([('instructor', 'email', 'type', 'course')]),
        ),
    ]
