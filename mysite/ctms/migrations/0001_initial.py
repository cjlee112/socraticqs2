# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ct', '0019_auto_20160614_0335'),
    ]

    operations = [
        migrations.CreateModel(
            name='SharedCourse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course', models.ForeignKey(to='ct.Course')),
                ('from_user', models.ForeignKey(related_name='my_shared_courses', to=settings.AUTH_USER_MODEL)),
                ('to_user', models.ForeignKey(related_name='shared_with_me', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
