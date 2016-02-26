# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import chat.utils
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0016_auto_20150626_0301'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Chat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_open', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EnrollUnitCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enrollCode', models.CharField(default=chat.utils.enroll_generator, max_length=32)),
                ('unit', models.ForeignKey(to='ct.Unit')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(default=datetime.datetime.now, null=True)),
                ('contenttype', models.CharField(default=b'NoneType', max_length=16, null=True, choices=[(b'NoneType', b'NoneType'), (b'divider', b'divider'), (b'response', b'response'), (b'lesson', b'lesson')])),
                ('content_id', models.IntegerField(null=True)),
                ('chat', models.OneToOneField(null=True, to='chat.Chat')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='enrollunitcode',
            unique_together=set([('enrollCode', 'unit')]),
        ),
        migrations.AddField(
            model_name='chat',
            name='next_step',
            field=models.OneToOneField(related_name='base_chat', null=True, to='chat.Message'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='chat',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
