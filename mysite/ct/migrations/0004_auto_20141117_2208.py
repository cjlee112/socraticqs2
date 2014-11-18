# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ct', '0003_auto_20141110_2153'),
    ]

    operations = [
        migrations.CreateModel(
            name='FAQ',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('response', models.ForeignKey(to='ct.Response')),
                ('unitLesson', models.ForeignKey(to='ct.UnitLesson')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InquiryCount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('response', models.ForeignKey(to='ct.Response')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Liked',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('atime', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'time submitted')),
                ('addedBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('unitLesson', models.ForeignKey(to='ct.UnitLesson')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='concept',
            name='description',
        ),
        migrations.AddField(
            model_name='lesson',
            name='concept',
            field=models.ForeignKey(to='ct.Concept', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='conceptlink',
            name='relationship',
            field=models.CharField(default=b'defines', max_length=10, choices=[(b'defines', b'Defines'), (b'tests', b'Tests understanding of'), (b'resol', b'Helps students resolve'), (b'derives', b'Derives'), (b'proves', b'Proves'), (b'assumes', b'Assumes'), (b'motiv', b'Motivates'), (b'illust', b'Illustrates'), (b'intro', b'Introduces'), (b'comment', b'Comments on'), (b'warns', b'Warns about')]),
        ),
        migrations.AlterField(
            model_name='response',
            name='course',
            field=models.ForeignKey(to='ct.Course'),
        ),
        migrations.AlterField(
            model_name='response',
            name='unitLesson',
            field=models.ForeignKey(to='ct.UnitLesson'),
        ),
        migrations.AlterField(
            model_name='studenterror',
            name='errorModel',
            field=models.ForeignKey(to='ct.UnitLesson'),
        ),
        migrations.AlterField(
            model_name='unitlesson',
            name='kind',
            field=models.CharField(default=b'part', max_length=10, choices=[(b'part', b'Included in this courselet'), (b'answers', b'Answer for a question'), (b'errmod', b'Common error for a question'), (b'resol', b'Resolution for an error'), (b'pretest', b'Pre-test/Post-test for this courselet'), (b'subunit', b'Container for this courselet')]),
        ),
    ]
