# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0014_fsmgroup'),
        ('fsm', '0001_initial')
    ]

    operations = [
        migrations.RemoveField(
            model_name='activityevent',
            name='activity',
        ),
        migrations.RemoveField(
            model_name='activityevent',
            name='unitLesson',
        ),
        migrations.RemoveField(
            model_name='activityevent',
            name='user',
        ),
        migrations.RemoveField(
            model_name='activitylog',
            name='course',
        ),
        migrations.RemoveField(
            model_name='fsm',
            name='addedBy',
        ),
        migrations.RemoveField(
            model_name='fsm',
            name='startNode',
        ),
        migrations.RemoveField(
            model_name='fsmedge',
            name='addedBy',
        ),
        migrations.RemoveField(
            model_name='fsmedge',
            name='fromNode',
        ),
        migrations.RemoveField(
            model_name='fsmedge',
            name='toNode',
        ),
        migrations.DeleteModel(
            name='FSMEdge',
        ),
        migrations.RemoveField(
            model_name='fsmgroup',
            name='fsm',
        ),
        migrations.DeleteModel(
            name='FSMGroup',
        ),
        migrations.RemoveField(
            model_name='fsmnode',
            name='addedBy',
        ),
        migrations.RemoveField(
            model_name='fsmnode',
            name='fsm',
        ),
        migrations.DeleteModel(
            name='FSM',
        ),
        migrations.RemoveField(
            model_name='fsmstate',
            name='activity',
        ),
        migrations.RemoveField(
            model_name='fsmstate',
            name='activityEvent',
        ),
        migrations.DeleteModel(
            name='ActivityEvent',
        ),
        migrations.RemoveField(
            model_name='fsmstate',
            name='fsmNode',
        ),
        migrations.DeleteModel(
            name='FSMNode',
        ),
        migrations.RemoveField(
            model_name='fsmstate',
            name='linkState',
        ),
        migrations.RemoveField(
            model_name='fsmstate',
            name='parentState',
        ),
        migrations.RemoveField(
            model_name='fsmstate',
            name='unitLesson',
        ),
        migrations.RemoveField(
            model_name='fsmstate',
            name='user',
        ),
        migrations.DeleteModel(
            name='FSMState',
        ),
        migrations.AlterField(
            model_name='response',
            name='activity',
            field=models.ForeignKey(to='fsm.ActivityLog', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='studenterror',
            name='activity',
            field=models.ForeignKey(to='fsm.ActivityLog', null=True),
            preserve_default=True,
        ),
        migrations.DeleteModel(
            name='ActivityLog',
        ),
    ]
