# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import provider.utils


class Migration(migrations.Migration):

    dependencies = [
        ('lti', '0004_auto_20150716_0259'),
    ]

    operations = [
        migrations.CreateModel(
            name='LtiConsumer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('consumer_name', models.CharField(unique=True, max_length=255)),
                ('consumer_key', models.CharField(default=provider.utils.short_token, unique=True, max_length=32, db_index=True)),
                ('consumer_secret', models.CharField(default=provider.utils.short_token, unique=True, max_length=32)),
                ('instance_guid', models.CharField(max_length=255, unique=True, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
