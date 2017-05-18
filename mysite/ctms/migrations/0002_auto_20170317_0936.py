# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ct', '0020_auto_20170412_0258'),
        ('accounts', '0002_auto_20160411_1313'),
        ('ctms', '0002_auto_20170302_0658'),
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
        migrations.AlterUniqueTogether(
            name='sharedcourse',
            unique_together=set([('from_user', 'to_user', 'course')]),
        ),
    ]
