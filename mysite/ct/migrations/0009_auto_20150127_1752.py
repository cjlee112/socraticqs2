from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('ct', '0008_auto_20150120_1407'),
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
        migrations.AddField(
            model_name='activityevent',
            name='activity',
            field=models.ForeignKey(to='ct.ActivityLog', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activityevent',
            name='unitLesson',
            field=models.ForeignKey(to='ct.UnitLesson', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsmnode',
            name='doLogging',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsmstate',
            name='activity',
            field=models.ForeignKey(to='ct.ActivityLog', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsmstate',
            name='activityEvent',
            field=models.ForeignKey(to='ct.ActivityEvent', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fsmstate',
            name='isLiveSession',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='response',
            name='activity',
            field=models.ForeignKey(to='ct.ActivityLog', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='studenterror',
            name='activity',
            field=models.ForeignKey(to='ct.ActivityLog', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
