# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
import chat.utils


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('fsm', '0002_auto_20150723_0243'),
        ('ct', '0018_unit_small_img_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='Chat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_open', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ChatDivider',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=64)),
                ('unitlesson', models.ForeignKey(to='ct.UnitLesson', null=True)),
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
                ('courseUnit', models.ForeignKey(to='ct.CourseUnit')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.TextField(null=True, blank=True)),
                ('timestamp', models.DateTimeField(null=True)),
                ('contenttype', models.CharField(default=b'NoneType', max_length=16, null=True, choices=[(b'NoneType', b'NoneType'), (b'chatdivider', b'chatdivider'), (b'response', b'response'), (b'unitlesson', b'unitlesson'), (b'uniterror', b'uniterror')])),
                ('content_id', models.IntegerField(null=True)),
                ('input_type', models.CharField(default=b'options', max_length=16, null=True, choices=[(b'text', b'text'), (b'options', b'options'), (b'custom', b'custom')])),
                ('type', models.CharField(default=b'message', max_length=16, choices=[(b'message', b'message'), (b'user', b'user'), (b'breakpoint', b'breakpoint')])),
                ('is_additional', models.BooleanField(default=False)),
                ('kind', models.CharField(max_length=32, null=True, choices=[(b'base', b'base'), (b'orct', b'orct'), (b'answer', b'answer'), (b'errmod', b'errmod'), (b'chatdivider', b'chatdivider'), (b'uniterror', b'uniterror'), (b'response', b'response'), (b'message', b'message'), (b'button', b'button')])),
                ('userMessage', models.BooleanField(default=False)),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='chat.Chat', null=True)),
                ('lesson_to_answer', models.ForeignKey(to='ct.UnitLesson', null=True)),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
                ('response_to_check', models.ForeignKey(to='ct.Response', null=True)),
                ('student_error', models.ForeignKey(to='ct.StudentError', null=True)),
            ],
            options={
                'ordering': ['timestamp'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UnitError',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('response', models.ForeignKey(to='ct.Response')),
                ('unit', models.ForeignKey(to='ct.Unit')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='enrollunitcode',
            unique_together=set([('enrollCode', 'courseUnit')]),
        ),
        migrations.AddField(
            model_name='chat',
            name='enroll_code',
            field=models.ForeignKey(to='chat.EnrollUnitCode', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='chat',
            name='instructor',
            field=models.ForeignKey(related_name='course_instructor', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='chat',
            name='next_point',
            field=models.OneToOneField(related_name='base_chat', null=True, to='chat.Message'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='chat',
            name='state',
            field=models.OneToOneField(null=True, to='fsm.FSMState'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='chat',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
