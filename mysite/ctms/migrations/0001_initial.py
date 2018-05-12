# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ct', '0024_auto_20180512_1527'),
        ('accounts', '0004_auto_20180405_1335'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invite',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=254)),
                ('code', models.CharField(max_length=255, verbose_name=b'invite code')),
                ('status', models.CharField(default=b'pending', max_length=20, verbose_name=b'status', choices=[(b'pendind', b'pending'), (b'joined', b'joined')])),
                ('type', models.CharField(default=b'tester', max_length=50, verbose_name=b'invite type', choices=[(b'student', b'student'), (b'tester', b'tester')])),
                ('added', models.DateTimeField(auto_now_add=True, verbose_name=b'added datetime')),
                ('course', models.ForeignKey(to='ct.Course')),
                ('instructor', models.ForeignKey(to='accounts.Instructor')),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='invite',
            unique_together=set([('instructor', 'email', 'type', 'course')]),
        ),
    ]
