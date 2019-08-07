from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ct', '0014_fsmgroup'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nodeName', models.CharField(max_length=64)),
                ('startTime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time created')),
                ('endTime', models.DateTimeField(null=True, verbose_name='time ended')),
                ('exitEvent', models.CharField(max_length=64)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fsmName', models.CharField(max_length=64)),
                ('startTime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time created')),
                ('endTime', models.DateTimeField(null=True, verbose_name='time ended')),
                ('course', models.ForeignKey(to='ct.Course', null=True, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FSM',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=64)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(null=True)),
                ('help', models.TextField(null=True)),
                ('hideTabs', models.BooleanField(default=False)),
                ('hideLinks', models.BooleanField(default=False)),
                ('hideNav', models.BooleanField(default=False)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FSMEdge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(null=True)),
                ('help', models.TextField(null=True)),
                ('showOption', models.BooleanField(default=False)),
                ('data', models.TextField(null=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FSMGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group', models.CharField(max_length=64)),
                ('fsm', models.ForeignKey(to='fsm.FSM', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FSMNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(null=True)),
                ('help', models.TextField(null=True)),
                ('path', models.CharField(max_length=200, null=True)),
                ('data', models.TextField(null=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time submitted')),
                ('funcName', models.CharField(max_length=200, null=True)),
                ('doLogging', models.BooleanField(default=False)),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('fsm', models.ForeignKey(to='fsm.FSM', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FSMState',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('path', models.CharField(max_length=200)),
                ('data', models.TextField(null=True)),
                ('hideTabs', models.BooleanField(default=False)),
                ('hideLinks', models.BooleanField(default=False)),
                ('hideNav', models.BooleanField(default=False)),
                ('isLiveSession', models.BooleanField(default=False)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='time started')),
                ('activity', models.ForeignKey(to='fsm.ActivityLog', null=True, on_delete=models.CASCADE)),
                ('activityEvent', models.ForeignKey(to='fsm.ActivityEvent', null=True, on_delete=models.CASCADE)),
                ('fsmNode', models.ForeignKey(to='fsm.FSMNode', on_delete=models.CASCADE)),
                ('linkState', models.ForeignKey(related_name='linkChildren', to='fsm.FSMState', null=True, on_delete=models.CASCADE)),
                ('parentState', models.ForeignKey(related_name='children', to='fsm.FSMState', null=True, on_delete=models.CASCADE)),
                ('unitLesson', models.ForeignKey(to='ct.UnitLesson', null=True, on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='fsmedge',
            name='fromNode',
            field=models.ForeignKey(related_name='outgoing', to='fsm.FSMNode', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsmedge',
            name='toNode',
            field=models.ForeignKey(related_name='incoming', to='fsm.FSMNode', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsm',
            name='startNode',
            field=models.ForeignKey(related_name='+', to='fsm.FSMNode', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activityevent',
            name='activity',
            field=models.ForeignKey(to='fsm.ActivityLog', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activityevent',
            name='unitLesson',
            field=models.ForeignKey(to='ct.UnitLesson', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activityevent',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
