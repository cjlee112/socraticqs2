# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chat', '0026_auto_20160407_0542'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='instructor',
            field=models.ForeignKey(related_name='course_instructor', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
