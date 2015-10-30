# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fsm', '0002_auto_20150723_0243'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activityevent',
            name='endTime',
            field=models.DateTimeField(null=True, verbose_name=b'time ended', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='activityevent',
            name='unitLesson',
            field=models.ForeignKey(blank=True, to='ct.UnitLesson', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='activitylog',
            name='course',
            field=models.ForeignKey(blank=True, to='ct.Course', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='activitylog',
            name='endTime',
            field=models.DateTimeField(null=True, verbose_name=b'time ended', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fsm',
            name='description',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fsm',
            name='help',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fsm',
            name='startNode',
            field=models.ForeignKey(related_name='+', blank=True, to='fsm.FSMNode', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fsmedge',
            name='data',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fsmedge',
            name='description',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fsmedge',
            name='help',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fsmnode',
            name='data',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fsmnode',
            name='description',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fsmnode',
            name='funcName',
            field=models.CharField(max_length=200, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fsmnode',
            name='help',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fsmnode',
            name='path',
            field=models.CharField(max_length=200, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fsmstate',
            name='activity',
            field=models.ForeignKey(blank=True, to='fsm.ActivityLog', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fsmstate',
            name='activityEvent',
            field=models.ForeignKey(blank=True, to='fsm.ActivityEvent', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fsmstate',
            name='data',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fsmstate',
            name='linkState',
            field=models.ForeignKey(related_name='linkChildren', blank=True, to='fsm.FSMState', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fsmstate',
            name='parentState',
            field=models.ForeignKey(related_name='children', blank=True, to='fsm.FSMState', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fsmstate',
            name='unitLesson',
            field=models.ForeignKey(blank=True, to='ct.UnitLesson', null=True),
            preserve_default=True,
        ),
    ]
