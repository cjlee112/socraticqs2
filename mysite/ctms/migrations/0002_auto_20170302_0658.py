# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('ctms', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sharedcourse',
            name='course',
            field=models.ForeignKey(related_name='shares', to='ct.Course'),
        ),
        migrations.AlterField(
            model_name='sharedcourse',
            name='from_user',
            field=models.ForeignKey(related_name='my_shares', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='sharedcourse',
            name='to_user',
            field=models.ForeignKey(related_name='shares_to_me', to=settings.AUTH_USER_MODEL),
        ),
    ]
